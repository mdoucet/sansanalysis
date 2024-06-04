# Django settings for sansanalysis project.
from __init__ import __version__
APP_DOMAIN = 'http://127.0.0.1:8000'
APP_VERSION = __version__
SAMPLE_LOCATION = 'simpleplot/test/'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/Users/mathieu/Documents/workspace/sansanalysis/demoDB'
    }
}

# The following is no longer used by django but is used by our OpenID app
DATABASE_ENGINE = 'sqlite3'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''
STATIC_ROOT = '/Users/mathieu/Documents/workspace/sansanalysis/static_root/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''
# To copy static files, do python manage.py collectstatic
STATIC_URL = '/media/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '8erjr$bajry+cv3arc(q^ko0ydim1%$30lq4zj)gz&ta6x42n!'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'sansanalysis.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "/Users/mathieu/Documents/workspace/sansanalysis/templates",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'sansanalysis.simpleplot',
    "django.contrib.admin",
    'sansanalysis.users',
    'sansanalysis.commenting',
    'sansanalysis.app_logging',
    'django.contrib.webdesign',
    #'sansanalysis.refl_invert',
    'sansanalysis.modeling',
    'django.contrib.staticfiles',

)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'sansanalysis.users.openid_backend.OpenIdBackend',
)

LOGIN_URL = '/users'
AUTH_PROFILE_MODULE = 'users.UserProfile'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    'django.core.context_processors.request',
)

