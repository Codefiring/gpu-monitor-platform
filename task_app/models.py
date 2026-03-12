"""
Task Management Models - Simplified for single server
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Task(models.Model):
    """GPU Task Model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField('Task Name', max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks', verbose_name='User')
    description = models.TextField('Description', blank=True)
    workspace = models.CharField('Working Directory', max_length=500, default='/home')
    command = models.TextField('Command to Execute')

    # GPU Requirements
    gpu_count = models.IntegerField(
        'Number of GPUs Required',
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(8)]
    )
    memory_required = models.IntegerField(
        'Memory Required (MB)',
        default=0,
        help_text='Minimum GPU memory required per GPU'
    )
    exclusive_gpu = models.BooleanField(
        'Exclusive GPU Access',
        default=True,
        help_text='If True, task will only run on GPUs with no other processes'
    )

    # Task Status
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField('Priority', default=0, help_text='Higher number = higher priority')

    # Execution Info
    assigned_gpus = models.CharField('Assigned GPUs', max_length=100, blank=True)
    pid = models.IntegerField('Process ID', null=True, blank=True)
    log_file = models.CharField('Log File Path', max_length=500, blank=True)

    # Timestamps
    created_at = models.DateTimeField('Created At', auto_now_add=True)
    started_at = models.DateTimeField('Started At', null=True, blank=True)
    completed_at = models.DateTimeField('Completed At', null=True, blank=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)

    class Meta:
        verbose_name = 'GPU Task'
        verbose_name_plural = 'GPU Tasks'
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username}) - {self.status}"

    @property
    def duration(self):
        """Calculate task duration"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_active(self):
        """Check if task is currently active"""
        return self.status in ['pending', 'running']


class TaskLog(models.Model):
    """Task execution log"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField('Timestamp', auto_now_add=True)
    level = models.CharField('Level', max_length=20, default='INFO')
    message = models.TextField('Message')

    class Meta:
        verbose_name = 'Task Log'
        verbose_name_plural = 'Task Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.task.name} - {self.level} - {self.timestamp}"
