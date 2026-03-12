from django.apps import AppConfig


class GpuAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gpu_app'
    verbose_name = 'GPU Monitoring'
