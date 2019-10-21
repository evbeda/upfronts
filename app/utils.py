from simple_salesforce import Salesforce
from textwrap import dedent

from . import (
    SF_DOMAIN,
    SF_PASSWORD,
    SF_SECURITY_TOKEN,
    SF_USERNAME,
)


def fetch_cases(comma_separated_case_numbers):
    sf = Salesforce(username=SF_USERNAME, password=SF_PASSWORD, security_token=SF_SECURITY_TOKEN, domain='test')
    case_numbers = comma_separated_case_numbers.split(',')
    case_numbers_querystring = ','.join(repr(str(num)) for num in case_numbers) if case_numbers else "''"
    cases = sf.query(
        'SELECT id, Contract__c, Description, CaseNumber, Case_URL__c from Case WHERE CaseNumber IN ({})'
        .format(case_numbers_querystring))['records']

    contract_ids = [c['Contract__c'] for c in cases]
    contract_ids_querystring = ','.join(repr(str(id)) for id in contract_ids)

    contracts = sf.query(
        'SELECT Eventbrite_Username__c, Hoopla_Account_Name__c, ActivatedDate from Contract WHERE id IN ({})'
        .format(contract_ids_querystring))['records']
    result = []

    for case, contract in zip(cases, contracts):
        result.append({
            'case_id': case['Id'],
            'case_number': case['CaseNumber'],
            'contract_id': case['Contract__c'],
            'description': case['Description'],
            'link_to_salesforce_case': case['Case_URL__c'],
            'organizer_email': contract['Eventbrite_Username__c'],
            'organizer_name': contract['Hoopla_Account_Name__c'],
            'signed_date': contract['ActivatedDate'],
        })
    return result


def get_case_by_id(case_id):
    sf = Salesforce(username=SF_USERNAME, password=SF_PASSWORD, security_token=SF_SECURITY_TOKEN, domain=SF_DOMAIN)
    case = sf.Case.get(case_id)
    return case


def get_contract_by_id(contract_id):
    sf = Salesforce(username=SF_USERNAME, password=SF_PASSWORD, security_token=SF_SECURITY_TOKEN, domain=SF_DOMAIN)
    contract = sf.Contract.get(contract_id)
    return contract


def fetch_cases_by_date(case_date_from, case_date_to):

    sf = Salesforce(username=SF_USERNAME, password=SF_PASSWORD, security_token=SF_SECURITY_TOKEN, domain=SF_DOMAIN)

    cases = sf.query(
        "SELECT id, Contract__c, Description, CaseNumber, Case_URL__c from Case WHERE (Subject LIKE '{r}' \
         OR Subject like '{n}') AND Contract__c != null"
        .format(r='RECOUPABLE%', n='NON-RECOUPABLE%'))['records']

    contracts_ids_query = "SELECT Contract__c from Case WHERE (Subject LIKE '{r}' OR Subject like '{n}') \
    AND Contract__c != null".format(r='RECOUPABLE%', n='NON-RECOUPABLE%')

    contracts = sf.query(
        "SELECT Id, Eventbrite_Username__c, Hoopla_Account_Name__c, ActivatedDate from Contract WHERE id IN ({q}) \
        AND BillingCountry = 'Brazil' AND ActivatedDate > {f} AND ActivatedDate < {t}"
        .format(q=contracts_ids_query, f=case_date_from, t=case_date_to))['records']

    result = []

    for case in cases:
        for contract in contracts:
            if case['Contract__c'] == contract['Id']:
                result.append({
                    'case_id': case['Id'],
                    'case_number': case['CaseNumber'],
                    'contract_id': case['Contract__c'],
                    'description': case['Description'],
                    'link_to_salesforce_case': case['Case_URL__c'],
                    'organizer_email': contract['Eventbrite_Username__c'],
                    'organizer_name': contract['Hoopla_Account_Name__c'],
                    'signed_date': contract['ActivatedDate'],
                })
    return result


def generate_presto_query(event_id=None, from_date=None, to_date=None):
    date_format = "%Y-%m-%d"
    from_date_condition = "and trx_date > '{}'".format(from_date.strftime(date_format)) if from_date else ""
    to_date_condition = "and trx_date < '{}'".format(to_date.strftime(date_format)) if to_date else ""
    event_id_condition = "and f.event_id = {}".format(event_id) if event_id else ""
    query = dedent("""
    select f.organizer_id, f.currency, u.email, e.name,
    sum(f_gts_ntv) as f_gts_ntv,
    sum(f_gtf_ntv) as f_gtf_ntv,
    sum(f_tax_ntv) as f_tax_ntv,
    sum(f_eb_tax_ntv) as f_eb_tax_ntv,
    sum(f_epp_gts_ntv) as f_epp_gts_ntv
    from hive.dw.f_ticket_merchandise_purchase f
    join hive.eb.users u on u.id = f.organizer_id
    join hive.eb.events e on e.id = f.event_id
    where f.currency in ('BRL')
    and is_valid = 'Y'
    {from_date_condition}
    {to_date_condition}
    {event_id_condition}
    group by 1,2,3,4
    """).format(
        from_date_condition=from_date_condition,
        to_date_condition=to_date_condition,
        event_id_condition=event_id_condition,
    )

    return query
