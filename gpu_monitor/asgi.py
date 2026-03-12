"""
ASGI config for gpu_monitor project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpu_monitor.settings')

application = get_asgi_application()
