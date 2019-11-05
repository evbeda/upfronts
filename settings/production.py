import dj_database_url
from settings import get_env_variable
from settings.base import *  # noqa


DEBUG = False

DB_FROM_ENV = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(DB_FROM_ENV)  # noqa

SOCIAL_AUTH_EVENTBRITE_KEY = get_env_variable('SOCIAL_AUTH_EVENTBRITE_KEY')
SOCIAL_AUTH_EVENTBRITE_SECRET = get_env_variable(
    'SOCIAL_AUTH_EVENTBRITE_SECRET',
)
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

DEFAULT_FILE_STORAGE = 'storages.backends.dropbox.DropBoxStorage'
DROPBOX_OAUTH2_TOKEN = get_env_variable('DROPBOX_OAUTH2_TOKEN')
DROPBOX_ROOT_PATH = '/Backup_Files'
