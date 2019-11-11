from settings import get_env_variable


INVALID_SIGN_DATE = '5678'
INVALID_RECOUP_AMOUNT = '1234A'
INVALID_PAYMENT_DATE = '28 DE OCTUBRE'

STATUS_INVESTED = 'INVESTED'
STATUS_COMMITED_APPROVED = 'COMMITED/APPROVED'

STATUS = [
    (STATUS_COMMITED_APPROVED, 'COMMITED/APPROVED'),
    (STATUS_INVESTED, 'INVESTED'),
]

SF_USERNAME = get_env_variable('SF_USERNAME')
SF_PASSWORD = get_env_variable('SF_PASSWORD')
SF_SECURITY_TOKEN = get_env_variable('SF_SECURITY_TOKEN')
SF_DOMAIN = get_env_variable('SF_DOMAIN')

LINK_TO_REPORT_EVENTS = "https://www.evbqa.com/myevent/{}/reports/attendee/"
LINK_TO_RECOUPS = "https://admin.eventbrite.com/admin/upfront_recoups/manage"
LINK_TO_SEARCH_EVENT_OR_USER = "https://admin.eventbrite.com/admin/search/?search_type=&search_query={email_organizer}"

BASIC_CONDITIONS = ('Promissory Note', 'Bank Details', 'Payment Date', 'Funds Available')

SUPERSET_QUERY_DATE_FORMAT = "%Y-%m-%d"
SUPERSET_DEFAULT_CURRENCY = 'BRL'

ITEMS_PER_PAGE = 15

DROPBOX_ERROR = "There was an error trying to connect with the file storage."
