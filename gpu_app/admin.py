"""
GPU App Admin Configuration
"""
from django.contrib import admin
from .models import GPUInfo


@admin.register(GPUInfo)
class GPUInfoAdmin(admin.ModelAdmin):
    list_display = ['index', 'name', 'utilization', 'memory_utilization_display',
                    'temperature', 'power_draw', 'is_occupied', 'updated_at']
    list_filter = ['is_available', 'is_occupied']
    readonly_fields = ['uuid', 'index', 'name', 'utilization', 'memory_total',
                       'memory_used', 'memory_free', 'temperature', 'power_draw',
                       'processes', 'updated_at']
    search_fields = ['name', 'uuid']

    def memory_utilization_display(self, obj):
        return f"{obj.memory_utilization}%"
    memory_utilization_display.short_description = 'Memory Usage'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
