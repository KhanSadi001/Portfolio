"""Vercel build step: set up the database so you never need to run commands yourself.

Runs on every deployment (Vercel calls it from pyproject.toml). Safe to run repeatedly.
"""
import os
import sys

import django
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def main():
    if not os.environ.get("DATABASE_URL"):
        print("build.py: DATABASE_URL is not set, skipping database setup.")
        return
    # Run migrations over the direct (unpooled) connection when Neon provides one;
    # schema changes are more reliable without the pooler in between.
    if os.environ.get("DATABASE_URL_UNPOOLED"):
        os.environ["DATABASE_URL"] = os.environ["DATABASE_URL_UNPOOLED"]
    django.setup()
    call_command("migrate", interactive=False)
    call_command("createcachetable")

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
    if username and password:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, os.environ.get("DJANGO_SUPERUSER_EMAIL", ""), password)
            print(f"build.py: created admin user '{username}'.")
    print("build.py: database ready.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # fail the deploy loudly rather than ship a broken site
        print(f"build.py failed: {exc}", file=sys.stderr)
        raise
