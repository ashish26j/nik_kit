"""
Django settings for Nik_kiT — P0 skeleton.

Config comes from environment variables (see infra/env/.env.example). Only what P0
needs is wired here; per-module apps get added as we build M01…M10.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

# --- Core ---------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=True)
# In dev the phone reaches Django at the laptop's LAN IP, so allow all hosts.
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

# --- Applications -------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "corsheaders",
    # local
    "apps.core",
    "apps.menu",
    "apps.accounts",
    "apps.orders",
    "apps.notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "nikkit.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "nikkit.wsgi.application"

# --- Database (MySQL) ---------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", default="nikkit"),
        "USER": env("DB_USER", default="nikkit"),
        "PASSWORD": env("DB_PASSWORD", default="nikkit_pw"),
        "HOST": env("DB_HOST", default="db"),
        "PORT": env("DB_PORT", default="3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# --- Auth / i18n / static -----------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ----------------------------------------------------------------------
# No global auth — endpoints opt in (client token) explicitly. This avoids
# SessionAuthentication's CSRF on our token/anon POSTs (register, cart).
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

# --- CORS (dev: allow the phone/browser to reach the API) ---------------------
from corsheaders.defaults import default_headers  # noqa: E402

CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)
# The web app sends a custom cart header; it must be allowed through CORS preflight.
CORS_ALLOW_HEADERS = (*default_headers, "x-cart-key")

# --- Payments & notifications (M06/M08) ---------------------------------------
# Manual UPI: the business UPI id shown in the QR, and where owner pings go.
BUSINESS_UPI_ID = env("BUSINESS_UPI_ID", default="nikkit@upi")
BUSINESS_CONTACT_EMAIL = env("BUSINESS_CONTACT_EMAIL", default="owner@nikkit.local")
# Dev: emails print to the container console. Swap for SMTP/WhatsApp later (M08 seam).
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
