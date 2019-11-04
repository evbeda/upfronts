import requests

from simple_salesforce import Salesforce
from textwrap import dedent

from app import (
    SF_DOMAIN,
    SF_PASSWORD,
    SF_SECURITY_TOKEN,
    SF_USERNAME,
    SUPERSET_QUERY_DATE_FORMAT,
)


class SalesforceQuery:

    def __init__(self):
        self.sf = Salesforce(username=SF_USERNAME, password=SF_PASSWORD, security_token=SF_SECURITY_TOKEN, domain=SF_DOMAIN)

    def fetch_cases(self, comma_separated_case_numbers):
        case_numbers = comma_separated_case_numbers.split(',')
        case_numbers_querystring = ','.join(repr(str(num)) for num in case_numbers) if case_numbers else "''"
        cases = self.sf.query(
            'SELECT id, Contract__c, Description, CaseNumber, Case_URL__c from Case WHERE CaseNumber IN ({})'
            .format(case_numbers_querystring))['records']

        contract_ids = [c['Contract__c'] for c in cases]
        contract_ids_querystring = ','.join(repr(str(id)) for id in contract_ids)

        contracts = self.sf.query(
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

    def get_case_by_id(self, case_id):
        case = self.sf.Case.get(case_id)
        return case

    def get_contract_by_id(self, contract_id):
        contract = self.sf.Contract.get(contract_id)
        return contract

    def fetch_cases_by_date(self, case_date_from, case_date_to):
        cases = self.sf.query(
            "SELECT id, Contract__c, Description, CaseNumber, Case_URL__c from Case WHERE (Subject LIKE '{r}' \
            OR Subject like '{n}') AND Contract__c != null"
            .format(r='RECOUPABLE%', n='NON-RECOUPABLE%'))['records']

        contracts_ids_query = "SELECT Contract__c from Case WHERE (Subject LIKE '{r}' OR Subject like '{n}') \
        AND Contract__c != null".format(r='RECOUPABLE%', n='NON-RECOUPABLE%')

        contracts = self.sf.query(
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

    def fetch_contract_attachments(self, contract_id):
        attachments = self.sf.query(
            "SELECT Id, Name, ContentType from Attachment WHERE ParentId = '{}'".format(contract_id))['records']

        result = []

        for attachment in attachments:
            result.append({
                'salesforce_id': attachment['Id'],
                'name': attachment['Name'],
                'content_type': attachment['ContentType'],
            })

        return result

    def fetch_attachment(self, attachment_id):
        session_Id = self.sf.session_id
        instance = self.sf.sf_instance
        contract_attachment = self.sf.Attachment.get(attachment_id)
        file_id = contract_attachment['Id']
        content_type = contract_attachment['ContentType']
        response = requests.get('https://' + instance + '/services/data/v39.0/sobjects/Attachment/' + file_id + '/body',
                                headers={'Content-Type': content_type, 'Authorization': 'Bearer ' + session_Id})
        return response


def generate_presto_query(vent_id=None, from_date=None, to_date=None, currency=None):
    currency = currency or 'BRL'
    from_date_condition = "AND trx_date > '{}'".format(
        from_date.strftime(SUPERSET_QUERY_DATE_FORMAT)
    ) if from_date else ""
    to_date_condition = "AND trx_date < '{}'".format(
        to_date.strftime(SUPERSET_QUERY_DATE_FORMAT)
    ) if to_date else ""
    event_id_condition = "AND f.event_id = {}".format(event_id) if event_id else ""
    currency = repr(currency)
    query = dedent("""
    SELECT  f.organizer_id,
            f.currency,
            u.email,
            e.name,
            sum(f_gts_ntv) AS f_gts_ntv,
            sum(f_gtf_ntv) AS f_gtf_ntv,
            sum(f_tax_ntv) AS f_tax_ntv,
            sum(f_eb_tax_ntv) AS f_eb_tax_ntv,
            sum(f_epp_gts_ntv) AS f_epp_gts_ntv

    FROM    hive.dw.f_ticket_merchandise_purchase f
            JOIN hive.eb.users u ON u.id = f.organizer_id
            JOIN hive.eb.events e ON e.id = f.event_id

    WHERE   is_valid = 'Y'
            AND f.currency IN ({currency})
            {from_date_condition}
            {to_date_condition}
            {event_id_condition}

    GROUP BY 1,2,3,4
    """).format(
        from_date_condition=from_date_condition,
        to_date_condition=to_date_condition,
        event_id_condition=event_id_condition,
        currency=currency,
    )

    return query

