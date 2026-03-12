"""
GPU App URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    path('gpu-status/', views.gpu_status, name='gpu_status'),
]
