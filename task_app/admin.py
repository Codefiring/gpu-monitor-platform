"""
Task App Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Task, TaskLog


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status_badge', 'gpu_count', 'priority',
                    'created_at', 'started_at', 'duration_display']
    list_filter = ['status', 'user', 'exclusive_gpu', 'created_at']
    search_fields = ['name', 'description', 'command']
    readonly_fields = ['pid', 'assigned_gpus', 'log_file', 'created_at',
                       'started_at', 'completed_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'user', 'description', 'status', 'priority')
        }),
        ('Execution Configuration', {
            'fields': ('workspace', 'command')
        }),
        ('GPU Requirements', {
            'fields': ('gpu_count', 'memory_required', 'exclusive_gpu')
        }),
        ('Execution Status', {
            'fields': ('pid', 'assigned_gpus', 'log_file')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at', 'updated_at')
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'running': '#007BFF',
            'completed': '#28A745',
            'failed': '#DC3545',
            'cancelled': '#6C757D',
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def duration_display(self, obj):
        if obj.duration:
            hours = int(obj.duration // 3600)
            minutes = int((obj.duration % 3600) // 60)
            seconds = int(obj.duration % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return '-'
    duration_display.short_description = 'Duration'


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    list_display = ['task', 'level', 'message_short', 'timestamp']
    list_filter = ['level', 'timestamp']
    search_fields = ['task__name', 'message']
    readonly_fields = ['task', 'timestamp', 'level', 'message']

    def message_short(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Message'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
