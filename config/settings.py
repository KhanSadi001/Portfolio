"""
Settings for Sadi Khan's portfolio.

Everything secret or environment-specific comes from environment variables,
which you set in the Vercel dashboard (Project > Settings > Environment Variables).
Locally, nothing is required: it falls back to SQLite and DEBUG mode.
"""
import os
from pathlib import Path

import dj_database_url
from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent

ON_VERCEL = bool(os.environ.get("VERCEL"))
DEBUG = os.environ.get("DJANGO_DEBUG", "0" if ON_VERCEL else "1") == "1"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("Set the DJANGO_SECRET_KEY environment variable.")
    SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".vercel.app"]
ALLOWED_HOSTS += [h.strip() for h in os.environ.get("EXTRA_ALLOWED_HOSTS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = ["https://*.vercel.app"] + [
    f"https://{h.lstrip('.')}" for h in os.environ.get("EXTRA_ALLOWED_HOSTS", "").split(",") if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.PageViewMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.csp",
            ],
        },
    },
]

# ---- Database ---------------------------------------------------------------
# Vercel's Neon integration sets DATABASE_URL automatically.
if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=0,          # serverless: don't hold connections open
            ssl_require=True,
        )
    }
    # Neon's DATABASE_URL goes through PgBouncer (transaction pooling),
    # which doesn't support the server-side cursors Django uses by default.
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

# The cache lives in the database so rate limits and the GitHub cache are shared
# by every serverless instance (an in-memory cache would reset constantly).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True

# ---- Static files -----------------------------------------------------------
# Vercel runs collectstatic automatically and serves STATIC_ROOT from its CDN.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Plain storage: Vercel serves the collected files from its CDN, but they aren't
    # bundled into the Django function, so a hashing/manifest storage can't find them
    # at runtime. Vercel gives each deployment fresh static URLs, so no hashing is needed.
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- Security ---------------------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False  # turn on only once you're sure about every subdomain

# Content Security Policy (Django's built-in CSP support).
# No inline scripts are used anywhere, so script-src can stay strict.
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF],
    "style-src": [CSP.SELF, "https://fonts.googleapis.com"],
    "font-src": [CSP.SELF, "https://fonts.gstatic.com"],
    "img-src": [CSP.SELF, "data:"],
    "connect-src": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
    "base-uri": [CSP.SELF],
    "form-action": [CSP.SELF],
    "object-src": [CSP.NONE],
}

# ---- App settings -----------------------------------------------------------
# Change the admin URL so bots scanning /admin/ find nothing.
ADMIN_PATH = os.environ.get("ADMIN_PATH", "manage-site").strip("/") + "/"

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "KhanSadi001")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")          # optional, raises API rate limit
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")      # optional, emails you new messages
CONTACT_TO_EMAIL = os.environ.get("CONTACT_TO_EMAIL", "businesswithsdk@gmail.com")
CONTACT_FROM_EMAIL = os.environ.get("CONTACT_FROM_EMAIL", "Portfolio <onboarding@resend.dev>")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}
