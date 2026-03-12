"""
GPU App Views - API endpoints for real-time monitoring
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import GPUInfo
from .utils import update_gpu_database


@require_http_methods(["GET"])
def gpu_status(request):
    """
    API endpoint to get current GPU status
    """
    # Update GPU info from nvidia-smi
    update_gpu_database()

    gpus = GPUInfo.objects.all().order_by('index')

    gpu_data = []
    for gpu in gpus:
        gpu_data.append({
            'index': gpu.index,
            'name': gpu.name,
            'uuid': gpu.uuid,
            'utilization': gpu.utilization,
            'memory_total': gpu.memory_total,
            'memory_used': gpu.memory_used,
            'memory_free': gpu.memory_free,
            'memory_utilization': gpu.memory_utilization,
            'temperature': gpu.temperature,
            'power_draw': gpu.power_draw,
            'processes': gpu.get_processes(),
            'is_occupied': gpu.is_occupied,
            'is_available': gpu.is_available,
        })

    return JsonResponse({
        'success': True,
        'gpus': gpu_data,
        'total_gpus': len(gpu_data)
    })
