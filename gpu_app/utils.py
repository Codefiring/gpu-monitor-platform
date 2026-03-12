"""
GPU Monitoring Utilities - Local GPU detection without SSH
"""
import subprocess
import json
import logging
from .models import GPUInfo

logger = logging.getLogger(__name__)


def get_local_gpu_info():
    """
    Get GPU information from local nvidia-smi command
    Returns list of GPU info dictionaries
    """
    try:
        # Query GPU basic info
        cmd = [
            'nvidia-smi',
            '--query-gpu=uuid,index,name,utilization.gpu,memory.total,memory.used,memory.free,temperature.gpu,power.draw',
            '--format=csv,noheader,nounits'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            logger.error(f"nvidia-smi failed: {result.stderr}")
            return []

        gpu_list = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 9:
                continue

            gpu_info = {
                'uuid': parts[0],
                'index': int(parts[1]),
                'name': parts[2],
                'utilization': int(float(parts[3])) if parts[3] else 0,
                'memory_total': int(float(parts[4])) if parts[4] else 0,
                'memory_used': int(float(parts[5])) if parts[5] else 0,
                'memory_free': int(float(parts[6])) if parts[6] else 0,
                'temperature': int(float(parts[7])) if parts[7] else 0,
                'power_draw': int(float(parts[8])) if parts[8] else 0,
                'processes': []
            }
            gpu_list.append(gpu_info)

        # Query running processes
        cmd_processes = [
            'nvidia-smi',
            '--query-compute-apps=gpu_uuid,pid,process_name,used_memory',
            '--format=csv,noheader,nounits'
        ]
        result_proc = subprocess.run(cmd_processes, capture_output=True, text=True, timeout=10)

        if result_proc.returncode == 0:
            # Create a mapping of GPU UUID to processes
            gpu_processes = {}
            for line in result_proc.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) < 4:
                    continue

                uuid = parts[0]
                process_info = {
                    'pid': int(parts[1]),
                    'name': parts[2],
                    'memory': int(float(parts[3])) if parts[3] else 0
                }

                # Get username for the process
                try:
                    ps_cmd = ['ps', '-o', 'user=', '-p', str(process_info['pid'])]
                    ps_result = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=5)
                    if ps_result.returncode == 0:
                        process_info['user'] = ps_result.stdout.strip()
                except:
                    process_info['user'] = 'unknown'

                if uuid not in gpu_processes:
                    gpu_processes[uuid] = []
                gpu_processes[uuid].append(process_info)

            # Add processes to GPU info
            for gpu in gpu_list:
                gpu['processes'] = gpu_processes.get(gpu['uuid'], [])

        return gpu_list

    except subprocess.TimeoutExpired:
        logger.error("nvidia-smi command timed out")
        return []
    except Exception as e:
        logger.error(f"Error getting GPU info: {e}")
        return []


def update_gpu_database():
    """
    Update GPU information in database
    """
    gpu_list = get_local_gpu_info()

    for gpu_data in gpu_list:
        try:
            gpu, created = GPUInfo.objects.update_or_create(
                uuid=gpu_data['uuid'],
                defaults={
                    'index': gpu_data['index'],
                    'name': gpu_data['name'],
                    'utilization': gpu_data['utilization'],
                    'memory_total': gpu_data['memory_total'],
                    'memory_used': gpu_data['memory_used'],
                    'memory_free': gpu_data['memory_free'],
                    'temperature': gpu_data['temperature'],
                    'power_draw': gpu_data['power_draw'],
                    'processes': json.dumps(gpu_data['processes']),
                    'is_available': True,
                }
            )

            if created:
                logger.info(f"Added new GPU: {gpu}")

        except Exception as e:
            logger.error(f"Error updating GPU {gpu_data.get('uuid')}: {e}")

    return len(gpu_list)


def find_available_gpus(num_gpus=1, memory_required=0, exclusive=True):
    """
    Find available GPUs for task allocation
    Returns list of GPU indices or None if not enough GPUs available
    """
    available = []

    for gpu in GPUInfo.objects.filter(is_available=True, is_occupied=False).order_by('index'):
        if gpu.is_free(memory_required, exclusive):
            available.append(gpu.index)
            if len(available) >= num_gpus:
                return available

    return None if len(available) < num_gpus else available


def mark_gpus_occupied(gpu_indices, occupied=True):
    """
    Mark GPUs as occupied or free
    """
    GPUInfo.objects.filter(index__in=gpu_indices).update(is_occupied=occupied)
