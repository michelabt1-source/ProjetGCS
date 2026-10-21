from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Réglages propres à la machine (serveur de production) : fichier .env à la racine,
# lignes CLE=valeur. Absent sur le poste de développement, où les valeurs par défaut s'appliquent.
_env_file = BASE_DIR / '.env'
if _env_file.exists():
    for _ligne in _env_file.read_text(encoding='utf-8').splitlines():
        _ligne = _ligne.strip()
        if _ligne and not _ligne.startswith('#') and '=' in _ligne:
            _cle, _valeur = _ligne.split('=', 1)
            os.environ.setdefault(_cle.strip(), _valeur.strip())


def _liste_env(nom, defaut=''):
    return [v.strip() for v in os.environ.get(nom, defaut).split(',') if v.strip()]


SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-k2c-=a&6(%+l0($1ghxfufy2c+^(2heid%_0)%#1qi7uszb^8@',
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'oui', 'yes')

ALLOWED_HOSTS = _liste_env('DJANGO_ALLOWED_HOSTS', '*')

# Origines autorisées pour les formulaires (ex. http://srv-hogip:8000,http://192.168.1.10:8000)
CSRF_TRUSTED_ORIGINS = _liste_env('DJANGO_CSRF_TRUSTED_ORIGINS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'matieres',
    'users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'compta_matieres.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'matieres.context_processors.fermer_url',
            ],
        },
    },
]

WSGI_APPLICATION = 'compta_matieres.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DJANGO_DB_PATH', BASE_DIR / 'db.sqlite3'),
        # Plusieurs utilisateurs simultanés : mode WAL et transactions IMMEDIATE
        # limitent les erreurs « database is locked ».
        'OPTIONS': {
            'timeout': 20,
            'transaction_mode': 'IMMEDIATE',
            'init_command': 'PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;',
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

# Séparateur de milliers « . » pour les montants (intcomma, floatformat:"…g").
# USE_THOUSAND_SEPARATOR reste désactivé : les identifiants et années ne sont pas groupés.
FORMAT_MODULE_PATH = ['compta_matieres.formats']

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Journal des erreurs serveur (indispensable quand DEBUG est désactivé)
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '{asctime} {levelname} {name} : {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
        'fichier': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'compta_matieres.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf-8',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {'handlers': ['console', 'fichier'], 'level': 'WARNING'},
    },
}
