import os
import sys

import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')
django.setup()

from core.models import StrategicPlanningSession


def reset_sessions():
    count = StrategicPlanningSession.objects.count()
    StrategicPlanningSession.objects.all().delete()
    print(f"Deleted {count} StrategicPlanningSession objects.")

if __name__ == '__main__':
    reset_sessions()
