import os


try:
    import django_jinja
    JINJA_INSTALLED = True
except ImportError:
    JINJA_INSTALLED = False


# Make filepaths relative to settings.
ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)  # noqa: E731

DEBUG = True
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

JINJA_CONFIG = {}

SITE_ID = 1
USE_I18N = False

SECRET_KEY = 'foobar'

DATABASES = {
    'default': {
        'NAME': 'test.db',
        'ENGINE': 'django.db.backends.sqlite3',
    },

    # Provide a readonly DB for testing DB replication scenarios.
    'readonly': {
        'NAME': 'test.readonly.db',
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'waffle',
    'test_app',
)

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'waffle.middleware.WaffleMiddleware',
)


ROOT_URLCONF = 'test_app.urls'

_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.template.context_processors.request',
    'django.contrib.messages.context_processors.messages',
)


if JINJA_INSTALLED:
    TEMPLATES = [
        {
            'BACKEND': 'django_jinja.backend.Jinja2',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'match_regex': r'jinja.*',
                'match_extension': '',
                'newstyle_gettext': True,
                'context_processors': _CONTEXT_PROCESSORS,
                'undefined': 'jinja2.Undefined',
                'extensions': [
                    'jinja2.ext.i18n',
                    'waffle.jinja.WaffleExtension',
                ],
            }
        }
    ]
else:
    TEMPLATES = []

TEMPLATES.append(
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': _CONTEXT_PROCESSORS,
        }
    }
)


WAFFLE_FLAG_DEFAULT = False
WAFFLE_SWITCH_DEFAULT = False
WAFFLE_SAMPLE_DEFAULT = False
WAFFLE_READ_FROM_WRITE_DB = False
WAFFLE_OVERRIDE = False
WAFFLE_ENABLE_ADMIN_PAGES = True
WAFFLE_CACHE_PREFIX = 'test:'
