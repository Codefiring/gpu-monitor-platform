"""
GPU Information Models - Simplified for single server
"""
from django.db import models
import json


class GPUInfo(models.Model):
    """Stores information about each GPU on the local server"""
    uuid = models.CharField('GPU UUID', max_length=100, primary_key=True)
    index = models.IntegerField('GPU Index')
    name = models.CharField('GPU Name', max_length=100)
    utilization = models.IntegerField('GPU Utilization (%)', default=0)
    memory_total = models.IntegerField('Total Memory (MB)', default=0)
    memory_used = models.IntegerField('Used Memory (MB)', default=0)
    memory_free = models.IntegerField('Free Memory (MB)', default=0)
    temperature = models.IntegerField('Temperature (C)', default=0)
    power_draw = models.IntegerField('Power Draw (W)', default=0)
    processes = models.TextField('Running Processes', default='[]')
    is_available = models.BooleanField('Available for Tasks', default=True)
    is_occupied = models.BooleanField('Occupied by Task', default=False)
    updated_at = models.DateTimeField('Last Updated', auto_now=True)

    class Meta:
        verbose_name = 'GPU Information'
        verbose_name_plural = 'GPU Information'
        ordering = ['index']

    def __str__(self):
        return f"GPU {self.index}: {self.name}"

    @property
    def memory_utilization(self):
        """Calculate memory utilization percentage"""
        if self.memory_total > 0:
            return int((self.memory_used / self.memory_total) * 100)
        return 0

    def get_processes(self):
        """Parse processes JSON"""
        try:
            return json.loads(self.processes)
        except:
            return []

    def is_free(self, memory_required=0, exclusive=True):
        """Check if GPU is free for task allocation"""
        if not self.is_available or self.is_occupied:
            return False

        if exclusive:
            # For exclusive mode, GPU must have no processes
            return len(self.get_processes()) == 0
        else:
            # For shared mode, check if enough memory is available
            return self.memory_free >= memory_required
