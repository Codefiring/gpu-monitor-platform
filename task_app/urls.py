"""
Task App URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/task-queue/', views.task_queue, name='task_queue'),
]
