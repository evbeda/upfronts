from upfronts import get_env_variable


INVALID_SIGN_DATE = '5678'
INVALID_RECOUP_AMOUNT = '1234A'
INVALID_PAYMENT_DATE = '28 DE OCTUBRE'

STATUS = [
    ('COMMITED/APPROVED', 'COMMITED/APPROVED'),
    ('PENDING', 'PENDING'),
]

SF_USERNAME = get_env_variable('SF_USERNAME')
SF_PASSWORD = get_env_variable('SF_PASSWORD')
SF_SECURITY_TOKEN = get_env_variable('SF_SECURITY_TOKEN')
SF_DOMAIN = get_env_variable('SF_DOMAIN')

LINK_TO_REPORT_EVENTS = "https://www.evbqa.com/myevent/{}/reports/attendee/"
LINK_TO_RECOUPS = "https://admin.eventbrite.com/admin/upfront_recoups/manage"
LINK_TO_SEARCH_EVENT_OR_USER = "https://admin.eventbrite.com/admin/search/?search_type=&search_query={email_organizer}"

BASIC_CONDITIONS = ('Promissory Note', 'Bank Details', 'Payment Date', 'Funds Available')
