from simple_salesforce import Salesforce
from . import (
    SF_USERNAME,
    SF_PASSWORD,
    SF_SECURITY_TOKEN,
)


def fetch_cases(comma_separated_case_numbers):
    sf = Salesforce(username=SF_USERNAME, password=SF_PASSWORD, security_token=SF_SECURITY_TOKEN, domain='test')
    case_numbers = comma_separated_case_numbers.split(',')
    case_numbers_querystring = ','.join(repr(str(num)) for num in case_numbers) if case_numbers else "''"
    cases = sf.query(
        'SELECT id, Contract__c, Description, CaseNumber from Case WHERE CaseNumber IN ({})'
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
            'eventbrite_username': contract['Eventbrite_Username__c'],
            'organizer_name': contract['Hoopla_Account_Name__c'],
            'signed_date': contract['ActivatedDate'],
        })
    return result
