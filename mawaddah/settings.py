import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _env(name: str) -> str:
    if name not in os.environ:
        raise ImproperlyConfigured(
            f"Required environment variable is missing: {name}. Add it to .env"
        )
    return os.environ[name]


def _env_bool(name: str) -> bool:
    v = _env(name).strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    raise ImproperlyConfigured(
        f"{name} must be a boolean (true/false); got {v!r}"
    )


def _env_int(name: str) -> int:
    raw = _env(name).strip()
    try:
        return int(raw)
    except ValueError as e:
        raise ImproperlyConfigured(f"{name} must be an integer") from e


def _env_csv(name: str) -> list[str]:
    return [x.strip() for x in _env(name).split(",") if x.strip()]


def _env_path(name: str) -> Path:
    raw = _env(name).strip()
    p = Path(raw)
    if p.is_absolute():
        return p
    return BASE_DIR / p


def _path_from_value(raw: str) -> Path:
    raw = raw.strip()
    p = Path(raw)
    if p.is_absolute():
        return p
    return BASE_DIR / p


# All values below come from .env only (no fallbacks in code).

SECRET_KEY = _env("DJANGO_SECRET_KEY")
DEBUG = _env_bool("DJANGO_DEBUG")
ALLOWED_HOSTS = _env_csv("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = _env_csv("DJANGO_CSRF_TRUSTED_ORIGINS")
# Read from .env; applied only when DEBUG is False (avoids redirect issues with runserver).
_SECURE_SSL_REDIRECT_ENV = _env_bool("DJANGO_SECURE_SSL_REDIRECT")

LANGUAGE_CODE = _env("DJANGO_LANGUAGE_CODE")
TIME_ZONE = _env("DJANGO_TIME_ZONE")
USE_I18N = _env_bool("DJANGO_USE_I18N")
USE_TZ = _env_bool("DJANGO_USE_TZ")

EMAIL_BACKEND = _env("DJANGO_EMAIL_BACKEND")

SITE_NAME = _env("DJANGO_SITE_NAME")
BREVO_API_KEY = _env("DJANGO_BREVO_API_KEY")
BREVO_SENDER_EMAIL = _env("DJANGO_BREVO_SENDER_EMAIL")
BREVO_SENDER_NAME = _env("DJANGO_BREVO_SENDER_NAME")
EMAIL_VERIFICATION_EXPIRE_HOURS = _env_int("DJANGO_EMAIL_VERIFICATION_EXPIRE_HOURS")
EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS = _env_int(
    "DJANGO_EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS"
)
_signup_domains_raw = _env("DJANGO_SIGNUP_ALLOWED_EMAIL_DOMAINS").strip()
SIGNUP_ALLOWED_EMAIL_DOMAINS = (
    None
    if not _signup_domains_raw
    else [x.strip().lower() for x in _signup_domains_raw.split(",") if x.strip()]
)

SITE_CANONICAL_URL = _env("DJANGO_SITE_CANONICAL_URL").strip().rstrip("/")
PRIVACY_POLICY_URL = _env("DJANGO_PRIVACY_POLICY_URL").strip()
PRAYER_CITY = _env("DJANGO_PRAYER_CITY").strip()
PRAYER_COUNTRY = _env("DJANGO_PRAYER_COUNTRY").strip()
PRAYER_CACHE_SECONDS = _env_int("DJANGO_PRAYER_CACHE_SECONDS")

DATABASES = {
    "default": {
        "ENGINE": _env("DJANGO_DATABASE_ENGINE"),
        "NAME": _env_path("DJANGO_DATABASE_NAME"),
    }
}

STATIC_URL = _env("DJANGO_STATIC_URL")
MEDIA_URL = _env("DJANGO_MEDIA_URL")
STATIC_ROOT = _env_path("DJANGO_STATIC_ROOT")
MEDIA_ROOT = _env_path("DJANGO_MEDIA_ROOT")
STATICFILES_DIRS = [
    _path_from_value(p)
    for p in _env("DJANGO_STATICFILES_DIRS").split(",")
    if p.strip()
]

if not DEBUG:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }

LOGIN_REDIRECT_URL = _env("DJANGO_LOGIN_REDIRECT_URL")
LOGOUT_REDIRECT_URL = _env("DJANGO_LOGOUT_REDIRECT_URL")
LOGIN_URL = _env("DJANGO_LOGIN_URL")

SESSION_COOKIE_HTTPONLY = _env_bool("DJANGO_SESSION_COOKIE_HTTPONLY")
CSRF_COOKIE_HTTPONLY = _env_bool("DJANGO_CSRF_COOKIE_HTTPONLY")
SECURE_BROWSER_XSS_FILTER = _env_bool("DJANGO_SECURE_BROWSER_XSS_FILTER")
X_FRAME_OPTIONS = _env("DJANGO_X_FRAME_OPTIONS")

SECURE_HSTS_SECONDS = _env_int("DJANGO_SECURE_HSTS_SECONDS")
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS")

# App structure (fixed in code).

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.accounts",
    "apps.profiles",
    "apps.matching",
    "apps.messaging",
    "apps.moderation",
    "apps.console",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "mawaddah.middleware.SuperuserAdminOnlyMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Production only: needs `pip install whitenoise` on the server. Omitted when DEBUG=True
# so local `runserver` works without installing whitenoise.
if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "mawaddah.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "mawaddah.context_processors.moderation_nav",
            ],
        },
    },
]

WSGI_APPLICATION = "mawaddah.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = _SECURE_SSL_REDIRECT_ENV
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
