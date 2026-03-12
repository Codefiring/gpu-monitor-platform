"""
WSGI config for gpu_monitor project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpu_monitor.settings')

application = get_wsgi_application()
