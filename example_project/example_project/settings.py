"""
Django settings for example_project - Django PostgreSQL Anonymizer Demo

This example project demonstrates how to integrate django-postgres-anonymizer
into a Django application.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    # python-dotenv not installed, will use environment variables
    pass

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-example-key-only-for-demo-purposes")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Django PostgreSQL Anonymizer
    "django_postgres_anon",
    # Example apps
    "sample_app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Django PostgreSQL Anonymizer Middleware
    "django_postgres_anon.middleware.AnonRoleMiddleware",
]

ROOT_URLCONF = "example_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "example_project.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("DB_NAME", "postgres_anon_example"),
        "USER": os.environ.get("DB_USER", "sanyamkhurana"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# Django PostgreSQL Anonymizer Settings
POSTGRES_ANON = {
    "ENABLED": os.getenv("ANON_ENABLED", "True").lower() in ("true", "1", "yes"),
    "AUTO_APPLY_RULES": os.getenv("ANON_AUTO_APPLY_RULES", "False").lower() in ("true", "1", "yes"),
    "VALIDATE_FUNCTIONS": os.getenv("ANON_VALIDATE_FUNCTIONS", "True").lower() in ("true", "1", "yes"),
    "ALLOW_CUSTOM_FUNCTIONS": os.getenv("ANON_ALLOW_CUSTOM_FUNCTIONS", "False").lower() in ("true", "1", "yes"),
    "ENABLE_LOGGING": os.getenv("ANON_ENABLE_LOGGING", "True").lower() in ("true", "1", "yes"),
    "DEFAULT_MASKED_ROLE": os.getenv("ANON_DEFAULT_MASKED_ROLE", "masked_reader"),
    "MASKED_GROUPS": os.getenv("ANON_MASKED_GROUPS", "view_masked_data,analysts,qa_team").split(","),
    "ANONYMIZED_DATA_ROLE": os.getenv("ANONYMIZED_DATA_ROLE", "masked_reader"),
}

# Security Settings (environment-configurable)
if not DEBUG:
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() in ("true", "1", "yes")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True").lower() in ("true", "1", "yes")
    CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True").lower() in ("true", "1", "yes")

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django_postgres_anon.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django_postgres_anon": {
            "handlers": ["console", "file"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": True,
        },
    },
}

# Authentication URLs for demo app
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/sample/"
