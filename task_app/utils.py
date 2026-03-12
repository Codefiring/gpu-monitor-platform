"""
Task Execution Utilities - Local execution without SSH
"""
import os
import subprocess
import signal
import logging
from datetime import datetime
from django.utils import timezone
from .models import Task, TaskLog
from gpu_app.utils import find_available_gpus, mark_gpus_occupied

logger = logging.getLogger(__name__)


class LocalTaskRunner:
    """Execute tasks locally on the server"""

    def __init__(self, task):
        self.task = task
        self.process = None
        self.log_file_path = None

    def prepare_log_file(self):
        """Create log file for task output"""
        log_dir = 'logs/tasks'
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"task_{self.task.id}_{self.task.name}_{timestamp}.log"
        self.log_file_path = os.path.join(log_dir, filename)

        return self.log_file_path

    def execute(self, gpu_indices):
        """
        Execute task on specified GPUs
        """
        try:
            # Prepare log file
            log_file = self.prepare_log_file()
            self.task.log_file = log_file
            self.task.assigned_gpus = ','.join(map(str, gpu_indices))
            self.task.save()

            # Prepare environment with CUDA_VISIBLE_DEVICES
            env = os.environ.copy()
            env['CUDA_VISIBLE_DEVICES'] = ','.join(map(str, gpu_indices))

            # Prepare command
            cmd = f"cd {self.task.workspace} && {self.task.command}"

            # Log task start
            TaskLog.objects.create(
                task=self.task,
                level='INFO',
                message=f"Starting task on GPUs: {gpu_indices}"
            )

            # Execute command
            with open(log_file, 'w') as log_f:
                log_f.write(f"Task: {self.task.name}\n")
                log_f.write(f"User: {self.task.user.username}\n")
                log_f.write(f"GPUs: {gpu_indices}\n")
                log_f.write(f"Command: {self.task.command}\n")
                log_f.write(f"Working Directory: {self.task.workspace}\n")
                log_f.write(f"Started at: {timezone.now()}\n")
                log_f.write("=" * 80 + "\n\n")
                log_f.flush()

                self.process = subprocess.Popen(
                    cmd,
                    shell=True,
                    env=env,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid  # Create new process group
                )

            # Update task status
            self.task.pid = self.process.pid
            self.task.status = 'running'
            self.task.started_at = timezone.now()
            self.task.save()

            # Mark GPUs as occupied
            mark_gpus_occupied(gpu_indices, occupied=True)

            logger.info(f"Task {self.task.id} started with PID {self.process.pid}")

            return True

        except Exception as e:
            logger.error(f"Error executing task {self.task.id}: {e}")
            TaskLog.objects.create(
                task=self.task,
                level='ERROR',
                message=f"Failed to start task: {str(e)}"
            )
            self.task.status = 'failed'
            self.task.save()
            return False

    def wait_for_completion(self):
        """Wait for task to complete and update status"""
        if not self.process:
            return

        try:
            return_code = self.process.wait()

            # Update task status based on return code
            if return_code == 0:
                self.task.status = 'completed'
                log_level = 'INFO'
                log_message = 'Task completed successfully'
            else:
                self.task.status = 'failed'
                log_level = 'ERROR'
                log_message = f'Task failed with return code {return_code}'

            self.task.completed_at = timezone.now()
            self.task.save()

            # Free GPUs
            if self.task.assigned_gpus:
                gpu_indices = [int(x) for x in self.task.assigned_gpus.split(',')]
                mark_gpus_occupied(gpu_indices, occupied=False)

            # Log completion
            TaskLog.objects.create(
                task=self.task,
                level=log_level,
                message=log_message
            )

            logger.info(f"Task {self.task.id} completed with status: {self.task.status}")

        except Exception as e:
            logger.error(f"Error waiting for task {self.task.id}: {e}")
            self.task.status = 'failed'
            self.task.completed_at = timezone.now()
            self.task.save()

    def kill(self):
        """Kill running task"""
        if self.process and self.process.poll() is None:
            try:
                # Kill entire process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                logger.info(f"Task {self.task.id} killed")

                self.task.status = 'cancelled'
                self.task.completed_at = timezone.now()
                self.task.save()

                # Free GPUs
                if self.task.assigned_gpus:
                    gpu_indices = [int(x) for x in self.task.assigned_gpus.split(',')]
                    mark_gpus_occupied(gpu_indices, occupied=False)

                TaskLog.objects.create(
                    task=self.task,
                    level='WARNING',
                    message='Task was cancelled'
                )

            except Exception as e:
                logger.error(f"Error killing task {self.task.id}: {e}")


def run_task(task):
    """
    Main function to run a task
    This will be called by the scheduler
    """
    # Find available GPUs
    gpu_indices = find_available_gpus(
        num_gpus=task.gpu_count,
        memory_required=task.memory_required,
        exclusive=task.exclusive_gpu
    )

    if gpu_indices is None:
        logger.info(f"No available GPUs for task {task.id}")
        return False

    # Execute task
    runner = LocalTaskRunner(task)
    if runner.execute(gpu_indices):
        # Wait for completion in the same thread
        # In production, this should be in a separate thread/process
        runner.wait_for_completion()
        return True

    return False
