"""
Task Scheduler - Simplified for single server
Continuously monitors pending tasks and schedules them on available GPUs
"""
import os
import sys
import time
import logging
import threading
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpu_monitor.settings')
django.setup()

from task_app.models import Task
from task_app.utils import run_task
from gpu_app.utils import update_gpu_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Main task scheduler"""

    def __init__(self, update_interval=10):
        self.update_interval = update_interval
        self.running = True
        self.active_threads = []

    def cleanup_threads(self):
        """Remove completed threads"""
        self.active_threads = [t for t in self.active_threads if t.is_alive()]

    def schedule_tasks(self):
        """Find pending tasks and schedule them if GPUs are available"""
        # Get pending tasks ordered by priority
        pending_tasks = Task.objects.filter(status='pending').order_by('-priority', 'created_at')

        for task in pending_tasks:
            # Run task in separate thread
            thread = threading.Thread(target=run_task, args=(task,))
            thread.daemon = True
            thread.start()
            self.active_threads.append(thread)

            logger.info(f"Scheduled task {task.id}: {task.name}")

            # Small delay between task starts
            time.sleep(2)

    def run(self):
        """Main scheduler loop"""
        logger.info("Task Scheduler started")

        while self.running:
            try:
                start_time = time.time()

                # Update GPU information
                num_gpus = update_gpu_database()
                logger.info(f"Updated {num_gpus} GPUs")

                # Cleanup completed threads
                self.cleanup_threads()
                logger.info(f"Active task threads: {len(self.active_threads)}")

                # Schedule pending tasks
                self.schedule_tasks()

                # Ensure minimum interval between cycles
                elapsed = time.time() - start_time
                if elapsed < self.update_interval:
                    time.sleep(self.update_interval - elapsed)

            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by user")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                time.sleep(self.update_interval)

        logger.info("Task Scheduler stopped")

    def stop(self):
        """Stop the scheduler"""
        self.running = False


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('logs/tasks', exist_ok=True)
    os.makedirs('data', exist_ok=True)

    # Start scheduler
    scheduler = TaskScheduler(update_interval=10)

    try:
        scheduler.run()
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        scheduler.stop()
        sys.exit(0)
