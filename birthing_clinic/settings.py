import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-change-this-in-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'patients',
    'prenatal',
    'appointments',
    'delivery',
    'newborn',
    'inventory',
    'billing',
    'reports',
    'auditlogs',
    'postpartum',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'auditlogs.middleware.AuditLogMiddleware',
    'auditlogs.middleware.CurrentUserMiddleware',
]

ROOT_URLCONF = 'birthing_clinic.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'birthing_clinic.context_processors.clinic_alerts',
                'birthing_clinic.context_processors.user_permissions',
            ],
        },
    },
]

WSGI_APPLICATION = 'birthing_clinic.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

SESSION_COOKIE_AGE = 28800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ── Email Configuration ───────────────────────────────────────────────────────
# Configure for production: change to django.core.mail.backends.smtp.EmailBackend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ''        # Set in environment: BIRTHCARE_EMAIL
EMAIL_HOST_PASSWORD = ''    # Set in environment: BIRTHCARE_EMAIL_PWD
DEFAULT_FROM_EMAIL = 'BirthCare Clinic <noreply@birthcare.ph>'

# ── Production Security Headers ─────────────────────────────────────────────
# These are safe to set now. SSL-specific ones activate only when DEBUG=False.
# For local dev, DEBUG=True so SSL redirect is skipped automatically.

X_FRAME_OPTIONS = 'SAMEORIGIN'          # Allow framing only from same origin
SECURE_CONTENT_TYPE_NOSNIFF = True       # Prevent MIME-sniffing
SECURE_BROWSER_XSS_FILTER = True         # Legacy XSS filter header
REFERRER_POLICY = 'strict-origin-when-cross-origin'

# These only activate in production (DEBUG=False):
SECURE_SSL_REDIRECT = not DEBUG          # Redirect HTTP → HTTPS
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000   # 1 year HSTS in prod
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG        # Cookie only sent over HTTPS in prod
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True           # JS cannot read session cookie
CSRF_COOKIE_HTTPONLY = False             # CSRF cookie needs to be readable
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Additional security middleware
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Content Security Policy (relaxed for inline styles/scripts used in templates)
# Tighten this per-route in production if needed
