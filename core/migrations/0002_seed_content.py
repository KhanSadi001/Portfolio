"""Loads the projects and blog posts that were on the original static site."""
import datetime

from django.db import migrations
from django.utils import timezone

PROJECTS = [
    # title, slug, category, tag, where, year, description, url, repo, featured, order
    ("Asteroid Threat Predictor", "asteroid-threat-predictor", "ml", "Machine learning", "Usman University of Technology", 2025,
     "A model and desktop app that predicts whether an asteroid is potentially hazardous.",
     "https://github.com/KhanSadi001/Asteroid-Threat-Predictor", "Asteroid-Threat-Predictor", True, 0),
    ("Simple Document Clustering", "document-clustering", "ml", "Machine learning", "Personal project", 2025,
     "Grouping text documents by topic with unsupervised learning.",
     "https://github.com/KhanSadi001/Simple-Document-Clustering", "Simple-Document-Clustering", True, 1),
    ("Dominant Color Extractor", "dominant-color-extractor", "ml", "Machine learning", "Personal project", 2025, "",
     "https://github.com/KhanSadi001/Dominant-Color-Extractor", "Dominant-Color-Extractor", False, 2),
    ("Arduino laser Li-Fi", "arduino-laser-lifi", "hardware", "Hardware", "Usman University of Technology", 2024,
     "Sending data between two Arduinos over a beam of light instead of radio.",
     "https://github.com/KhanSadi001/Arduino-Laser-LIFI-Transmission", "Arduino-Laser-LIFI-Transmission", True, 0),
    ("Data science & ML projects", "datacamp-portfolio", "ml", "Data science", "DataCamp portfolio", 2024, "",
     "https://www.datacamp.com/portfolio/msaadikh", "", False, 1),
    ("Bus Management System", "bus-management-system", "python", "Python", "Usman University of Technology", 2023, "",
     "https://github.com/KhanSadi001/Bus-Management-System", "Bus-Management-System", False, 0),
    ("Web scraping with Scrapy", "web-scraping-scrapy", "python", "Python", "Personal project", 2023, "",
     "https://github.com/KhanSadi001/Data-Scraping-through-Scrapy.", "Data-Scraping-through-Scrapy.", False, 1),
    ("Django Weather App", "django-weather-app", "python", "Django", "Personal project", 2022, "",
     "https://github.com/KhanSadi001/django_weather_app", "django_weather_app", False, 0),
    ("Django Social Media App", "django-social-media-app", "python", "Django", "Personal project", 2022, "",
     "https://github.com/KhanSadi001/Social-Media-App-with-Django", "Social-Media-App-with-Django", False, 1),
    ("Arduino Radar System", "arduino-radar", "hardware", "Hardware", "Aptech Learning", 2022, "",
     "https://github.com/KhanSadi001/Arduino-Radar", "Arduino-Radar", False, 2),
]

POSTS = [
    ("freedom-of-speech", "YESSSSSSSS FREEDOM OF SPEECH SOMEWHERE!!!!!", datetime.date(2024, 12, 22)),
    ("start-working-today", "If you want to become a better computer scientist, start working from today 😉", datetime.date(2024, 12, 15)),
]


def load(apps, schema_editor):
    Project = apps.get_model("core", "Project")
    Post = apps.get_model("core", "Post")
    for (title, slug, cat, tag, where, year, desc, url, repo, featured, order) in PROJECTS:
        Project.objects.get_or_create(slug=slug, defaults=dict(
            title=title, category=cat, tag=tag, where=where, year=year, description=desc,
            url=url, github_repo=repo, featured=featured, order=order,
        ))
    tz = timezone.get_default_timezone()
    for slug, body, day in POSTS:
        Post.objects.get_or_create(slug=slug, defaults=dict(
            body=body, published_at=datetime.datetime.combine(day, datetime.time(12, 0), tzinfo=tz),
        ))


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(load, migrations.RunPython.noop)]
