import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")
# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
django.setup()
from datetime import date, timedelta

from core.models import Project, WeatherSnapshot
from core.tasks import update_daily_weather_snapshots

# Create a fresh project
today = date.today()
project = Project.objects.create(
    name="Debug Weather Project",
    address="123 Main St",
    start_date=today - timedelta(days=1),
    end_date=today + timedelta(days=10),
)

result = update_daily_weather_snapshots()
print("result:", result)
print("created snapshot for project?", WeatherSnapshot.objects.filter(project=project, date=today).exists())
print(
    "matching snapshots:",
    list(WeatherSnapshot.objects.filter(project=project, date=today).values("id", "source", "date")),
)
