import os
from settings import get_env_variable
from settings.base import *  # noqa


DEBUG = True

SOCIAL_AUTH_EVENTBRITE_KEY = get_env_variable('SOCIAL_AUTH_EVENTBRITE_KEY')
SOCIAL_AUTH_EVENTBRITE_SECRET = get_env_variable(
    'SOCIAL_AUTH_EVENTBRITE_SECRET',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),  # noqa
    }
}

DEFAULT_FILE_STORAGE = 'storages.backends.dropbox.DropBoxStorage'
DROPBOX_OAUTH2_TOKEN = get_env_variable('DROPBOX_OAUTH2_TOKEN')
DROPBOX_ROOT_PATH = '/Backup_Files'
