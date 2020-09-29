"""Base settings to build other settings off."""

# ===============================================================================
# THIRD_PARTY IMPORTS
# ===============================================================================
import dill
from django.contrib.sessions import serializers
from django.core.cache.backends import locmem
from pathlib import Path
import environ


ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

env = environ.Env()

DOT_ENV_FILE = env("DOT_ENV_FILE", default="production")

# Read a base env file, then overwrite with env-specific variables
env.read_env(str(ROOT_DIR / ".envs" / "base"))
env.read_env(str(ROOT_DIR / ".envs" / DOT_ENV_FILE))

DEBUG = env.bool("DJANGO_DEBUG", False)
TEMPLATE_DEBUG = DEBUG
CRISPY_FAIL_SILENTLY = not DEBUG

# Change the Pickle Serializer to use dill.
serializers.pickle = dill  # noqa
locmem.pickle = dill  # noqa

# ===============================================================================
# DATABASE SETTINGS
# ===============================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        "NAME": str(ROOT_DIR / "db"),  # Or path to database file if using sqlite3.
        "USER": "",  # Not used with sqlite3.
        "PASSWORD": "",  # Not used with sqlite3.
        "HOST": "",  # Set to empty string for localhost. Not used with sqlite3.
        "PORT": "",  # Set to empty string for default. Not used with sqlite3.
    }
}

# ===============================================================================
# INSTALLED APPS
# ===============================================================================
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "analytical",
    "crispy_forms",
    "halomod_app",
    "bootstrap_modal_forms",
]

# ===============================================================================
# CRISPY SETTINGS
# ===============================================================================

CRISPY_TEMPLATE_PACK = "bootstrap4"

# ===============================================================================
# LOGGING SETUP
# ===============================================================================


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
    },
    "handlers": {
        "console_dev": {
            "level": env("LOG_LEVEL", default="ERROR"),
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        },
        "console_prod": {
            "level": "INFO",
            "filters": ["require_debug_false"],
            "class": "logging.StreamHandler",
        },
    },
    "root": {"level": "INFO", "handlers": ["console_dev", "console_prod"]},
    "loggers": {
        "django.request": {
            "handlers": ["console_dev", "console_prod"],
            "level": "INFO",
            "propagate": True,
        },
        "halomod_app": {"handlers": ["console_dev", "console_prod"], "level": "INFO"},
    },
}

# ===============================================================================
# LOCALE SETTINGS
# ===============================================================================
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "UTC"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# ===============================================================================
# HOW TO GET TO MEDIA/STATIC FILES
# ===============================================================================
# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = "/media/"

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

STATIC_ROOT = str(ROOT_DIR / "static")
MEDIA_ROOT = str(ROOT_DIR / "media")

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "django.contrib.staticfiles.finders.DefaultStorageFinder",
)

# ===============================================================================
# TEMPLATES ETC.
# ===============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [ROOT_DIR / "templates"],
        "APP_DIRS": True,
    }
]

# ===============================================================================
# MISCELLANEOUS
# ===============================================================================
MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "TheHaloMod.urls"
SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "TheHaloMod.wsgi.application"
SESSION_SAVE_EVERY_REQUEST = True

# Use a local-memory cache session engine. If we don't do this,
# the session objects (which can be quite large, since we're pickling full halomodel
# instances) are saved to the db. This is bad firstly because it's slow, and secondly
# because the db get's filled up with stuff we never want to commit to git.
# On the actual site, we should probably use memcached instead of the locmem cache.
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# ==============================================================================
# SECURITY
# ==============================================================================
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"


# ===============================================================================
# EMAIL SETUP
# ===============================================================================
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)

# ===============================================================================
# REST Framework
# ===============================================================================
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}
