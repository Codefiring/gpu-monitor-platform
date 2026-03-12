"""
Task App Views
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Task


@login_required
def dashboard(request):
    """Main dashboard view"""
    return render(request, 'dashboard.html')


@require_http_methods(["GET"])
def task_queue(request):
    """API endpoint to get task queue status"""
    tasks = Task.objects.filter(status__in=['pending', 'running']).select_related('user')

    task_data = []
    for task in tasks:
        task_data.append({
            'id': task.id,
            'name': task.name,
            'user': task.user.username,
            'status': task.status,
            'gpu_count': task.gpu_count,
            'assigned_gpus': task.assigned_gpus,
            'priority': task.priority,
            'created_at': task.created_at.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'tasks': task_data,
        'total': len(task_data)
    })
