from pathlib import Path
from django.core.asgi import get_asgi_application
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms_project.settings')
application = get_asgi_application()
