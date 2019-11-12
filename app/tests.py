import base64
import csv
import datetime
import io
import mock
import requests
from textwrap import dedent
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)
from django.contrib.auth.models import (
    User,
)
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import ValidationError
from django.core.files import File
from django.test import (
    Client,
    RequestFactory,
    TestCase,
)
from django.urls import reverse
from freezegun import freeze_time

from app.factories import (
    AttachmentFactory,
    ContractFactory,
    EventFactory,
    InstallmentConditionFactory,
    InstallmentFactory,
)
from app import (
    INVALID_SIGN_DATE,
    INVALID_PAYMENT_DATE,
    INVALID_RECOUP_AMOUNT,
    ITEMS_PER_PAGE,
    STATUS,
    SUPERSET_QUERY_DATE_FORMAT,
)
from app.forms import CustomAuthenticationForm
from app.views import (
    AllInstallmentsView,
    ConditionBackupProofView,
    ConditionView,
    ContractAdd,
    ContractsFilter,
    ContractsTableView,
    CreateEvent,
    DeleteEvent,
    DeleteUploadedFileCondition,
    DetailContractView,
    InstallmentDelete,
    InstallmentsFilter,
    InstallmentUpdate,
    InstallmentView,
    SaveCaseView,
    ToggleConditionView,
)
from app.models import (
    Contract,
    Event,
    Installment,
    InstallmentCondition,
)
from app.utils import (
    generate_presto_query,
    SalesforceQuery,
)


def _generate_fake_salesforce_query_instance():
    with patch.object(SalesforceQuery, '__init__', return_value=None):
        sfq = SalesforceQuery()
    sfq.sf = Mock()
    sfq.sf.session_id = "FAKE_SESSION_ID"
    sfq.sf.sf_instance = "FAKE_INSTANCE"
    return sfq


class ModelTest(TestCase):

    def test_create_valid_contract(self):
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
            'description': 'some description',
            'case_number': '345978',
            'salesforce_id': '23465789',
            'salesforce_case_id': '4680990',
            'link_to_salesforce_case': 'https://pe33.zzxxzzz.com/5348fObs',
        }
        contract = Contract(**contract_data)
        contract.full_clean()
        contract_data.pop('signed_date')
        contract.full_clean()

    def test_create_invalid_contract(self):
        contract_data = {
            'organizer_email': '1234',
            'signed_date': INVALID_SIGN_DATE,
            'description': 'some description',
            'case_number': '345978',
            'salesforce_id': '23465789',
            'salesforce_case_id': '4680990',
        }

        expected_error_dict_messages = {
            'link_to_salesforce_case': ['This field cannot be blank.'],
            'organizer_account_name': ['This field cannot be blank.'],
            'organizer_email': ['Enter a valid email address.'],
            'signed_date': [
                "'{}' value has an invalid date format. "
                "It must be in YYYY-MM-DD format.".format(INVALID_SIGN_DATE)]
        }

        contract = Contract(**contract_data)
        with self.assertRaises(ValidationError) as cm:
            contract.full_clean()

        self.assertEqual(expected_error_dict_messages, cm.exception.message_dict)


class ContractTest(TestCase):

    def setUp(self):
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
        }
        self.contract = Contract.objects.create(**contract_data)

    def test_create_valid_installment(self):
        installment_data = {
            'contract': self.contract,
            'is_recoup': False,
            'status': STATUS[1][0],
            'upfront_projection': 9000,
            'maximum_payment_date': '2019-09-14',
            'payment_date': '2019-09-10',
            'recoup_amount': 14000,
            'gtf': 3500,
            'gts': 10000,
        }
        installment = Installment(**installment_data)
        installment.full_clean()

    def test_create_invalid_installment(self):
        installment_data = {
            'is_recoup': False,
            'upfront_projection': 9000,
            'maximum_payment_date': INVALID_PAYMENT_DATE,
            'payment_date': '2019-09-10',
            'recoup_amount': INVALID_RECOUP_AMOUNT,
            'gts': 10000,
        }
        expected_error_dict_messages = {
            'contract': ['This field cannot be null.'],
            'maximum_payment_date': [
                "'{}' value has an invalid date format. It must be in YYYY-MM-DD format.".format(INVALID_PAYMENT_DATE)],
            'recoup_amount': ["'{}' value must be a decimal number.".format(INVALID_RECOUP_AMOUNT)],
        }
        installment = Installment(**installment_data)
        with self.assertRaises(ValidationError) as cm:
            installment.full_clean()
        self.assertEqual(expected_error_dict_messages, cm.exception.message_dict)


class InstallmentConditionTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
        }
        self.contract = Contract.objects.create(**contract_data)
        installment_data = {
            'contract': self.contract,
            'is_recoup': False,
            'status': 'PENDING',
            'upfront_projection': 9000,
            'maximum_payment_date': '2019-09-14',
            'payment_date': '2019-09-10',
            'recoup_amount': 14000,
            'gtf': 3500,
            'gts': 10000,
        }
        self.installment = Installment.objects.create(**installment_data)

    def test_create_valid_installment_condition(self):
        installment_condition_data = {
            'condition_name': 'TEST_CONDITION_NAME',
            'installment': self.installment,
        }
        installment_condition = InstallmentCondition(**installment_condition_data)
        installment_condition.full_clean()

    def test_create_installment_condition_without_installment(self):
        installment_condition_data = {
            'condition_name': 'TEST_CONDITION_NAME',
        }
        expected_response = {
            'installment': ['This field cannot be null.'],
        }
        installment_condition = InstallmentCondition(**installment_condition_data)
        with self.assertRaises(ValidationError) as cm:
            installment_condition.full_clean()
        self.assertEqual(expected_response, cm.exception.message_dict)

    def test_toggle_condition_method(self):
        FREEZED_TIME = datetime.datetime(year=2019, month=8, day=20, hour=16, minute=30)
        condition_data = {
            'condition_name': 'TEST_CONDITION_NAME',
            'installment': self.installment,
        }
        condition = InstallmentCondition.objects.create(**condition_data)
        self.assertEqual(condition.done, None)
        with freeze_time(FREEZED_TIME):
            condition.toggle_done()
        self.assertEqual(condition.done, FREEZED_TIME)
        condition.toggle_done()
        self.assertIsNone(condition.done)

    def test_condition_view(self):
        TEST_CONDITION_NAME = 'TEST_CONDITION_NAME'
        installment_condition_data = {
            'condition_name': TEST_CONDITION_NAME,
            'installment': self.installment,
        }
        InstallmentCondition.objects.create(**installment_condition_data)
        kwargs = {
            'contract_id': self.contract.id,
            'installment_id': self.installment.id,
        }
        request = self.factory.get(reverse('conditions', kwargs=kwargs))
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        response = ConditionView.as_view()(request, **kwargs)
        content = response.render().content
        self.assertIn(bytes(TEST_CONDITION_NAME, encoding='utf-8'), content)

    def test_toggle_condition_view(self):
        installment_condition_data = {
            'condition_name': 'TEST_CONDITION_NAME',
            'installment': self.installment,
        }
        installment_condition = InstallmentCondition.objects.create(**installment_condition_data)
        self.assertEqual(installment_condition.done, None)
        kwargs = {
            'contract_id': self.contract.id,
            'installment_id': self.installment.id,
            'condition_id': installment_condition.id,
        }
        request = self.factory.post(reverse('toggle-condition', kwargs=kwargs))
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        ToggleConditionView.as_view()(request, **kwargs)
        installment_condition.refresh_from_db()
        self.assertNotEqual(installment_condition.done, None)


class RedirectTest(TestCase):

    def test_redirect_to_login_when_login_is_required(self):
        c = Client()
        response = c.get(reverse('contracts'))
        self.assertIn(reverse('login'), response.url)


class FilterTest(TestCase):

    def test_filter_text(self):
        contract1 = Contract.objects.create(
            organizer_account_name='EDA',
            organizer_email='test@test.com',
            signed_date='2019-03-20',
            case_number='633457357',
        )
        contract2 = Contract.objects.create(
            organizer_account_name='NOT_AN_INTERESTING_NAME',
            organizer_email='test@test.com',
            signed_date='2019-03-15',
            case_number='984534089',
        )
        contract3 = Contract.objects.create(
            organizer_account_name='NOT_AN_INTERESTING_NAME',
            organizer_email='test@eda.com',
            signed_date='2019-03-15',
            case_number='53498985fh2',
        )
        qs = Contract.objects.all()
        f = ContractsFilter()
        result = f.search_organizer(qs, '', 'EDA')
        self.assertIn(contract1, result)
        self.assertIn(contract3, result)
        self.assertNotIn(contract2, result)


class TableTest(TestCase):

    def test_installment_table(self):
        factory = RequestFactory()
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
        }
        contract = Contract.objects.create(**contract_data)
        installment_data = {
            'contract': contract,
            'is_recoup': False,
            'status': 'PENDING',
            'upfront_projection': 9000,
            'maximum_payment_date': '2019-09-14',
            'payment_date': '2019-09-10',
            'recoup_amount': 14000,
            'gtf': 3500,
            'gts': 10000,
        }
        self.installment = Installment.objects.create(**installment_data)
        installment_condition_data = {
            'condition_name': 'TEST_CONDITION_NAME',
            'installment': self.installment,
        }
        self.installment_condition = InstallmentCondition.objects.create(**installment_condition_data)
        request = factory.get('/contracts/')
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        response = ContractsTableView.as_view()(request)
        content = response.render().content
        self.assertIn(bytes(contract_data['organizer_account_name'], encoding='utf-8'), content)


class UpdateContractTest(TestCase):

    def test_update_contract(self):
        factory = RequestFactory()
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
        }
        contract = Contract.objects.create(**contract_data)
        contract_data['user_id'] = '234523'
        request = factory.post(
            reverse('contracts-update', args=[contract.id]), contract_data, content_type='application/json')
        self.assertIn(bytes(contract_data['user_id'], encoding='utf-8'), request.body)


class TestDownloadCsv(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.contract_data = {
            'organizer_account_name': 'EDA',
            'organizer_email': 'juan@eventbrite.com',
            'signed_date': '2019-04-04',
        }
        self.contract = Contract.objects.create(**self.contract_data)
        self.installment_data = {
            'contract_id': self.contract.id,
            'is_recoup': True,
            'status': 'COMMITED/APPROVED',
            'upfront_projection': 77777,
            'maximum_payment_date': '2019-05-30',
            'payment_date': '2019-05-05',
            'recoup_amount': 55555,
            'gtf': 100000,
            'gts': 7000,
        }
        self.installment = Installment.objects.create(**self.installment_data)

    def test_status_code_200(self):
        request = self.factory.get(reverse('all-installments'))
        request.path = request.path+'?download=true'
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        response = AllInstallmentsView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_download_csv(self):
        user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        self.client.force_login(user)
        kwargs = {
            'download': 'true',
        }

        response = self.client.get(reverse('all-installments'), kwargs)

        self.assertEqual('text/csv', response.get('Content-Type'))
        self.assertIn('-installments.csv', response.get('Content-Disposition'))

    def test_download_csv_without_filter(self):
        user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        kwargs = {
            'download': 'true',
        }

        self.client.force_login(user)
        response = self.client.get(reverse('all-installments'), kwargs)
        decoded_response = response.content.decode('utf-8')
        reader = csv.reader(io.StringIO(decoded_response))
        next(reader)
        csv_rows = [row for row in reader]
        self.assertEqual(len(Installment.objects.all()), len(csv_rows))

    def test_download_csv_with_filter(self):
        FILTERED_STATUS = 'COMMITED/APPROVED'
        NON_FILTERED_STATUS = 'PENDING'
        Installment.objects.create(
            contract=self.contract,
            is_recoup=True,
            status=NON_FILTERED_STATUS,
            upfront_projection=77777,
            maximum_payment_date='2019-05-30',
            payment_date='2019-05-05',
            recoup_amount=55555,
            gtf=100000,
            gts=7000,
        )
        user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        kwargs = {
            'search_organizer': '',
            'djfdate_time_signed_date': '',
            'djfdate_time_max_payment_date': '',
            'djfdate_ttime_payment_date': '',
            'status': FILTERED_STATUS,
            'download': 'true',
        }

        self.client.force_login(user)
        response = self.client.get(reverse('all-installments'), kwargs)

        decoded_response = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded_response))
        for row in reader:
            self.assertEqual(row['status'], FILTERED_STATUS)


class FetchCaseTests(TestCase):
    def test_fetch_cases_by_case_number(self):
        FAKE_SF_QUERY_RESPONSES = (
            {
                'records': [
                    {
                        'Id': 'FAKE_CASE_ID_1',
                        'CaseNumber': 'FAKE_CASE_NUMBER_1',
                        'Contract__c': 'FAKE_CONTRACT_ID_1',
                        'Description': 'FAKE_DESCRIPTION_1',
                        'Case_URL__c': 'https://pe33.zzxxzzz.com/5348fObs',
                    },
                    {
                        'Id': 'FAKE_CASE_ID_2',
                        'CaseNumber': 'FAKE_CASE_NUMBER_2',
                        'Contract__c': 'FAKE_CONTRACT_ID_2',
                        'Description': 'FAKE_DESCRIPTION_2',
                        'Case_URL__c': 'https://pe33.zzxxzzz.com/5348fObs',
                    },
                 ]
            },
            {
                'records': [
                    {
                        'Eventbrite_Username__c': 'FAKE_EVENTBRITE_USERNAME_1',
                        'Hoopla_Account_Name__c': 'FAKE_ACCOUNT_NAME_1',
                        'ActivatedDate': 'FAKE_SIGNED_DATE_1',
                    },
                    {
                        'Eventbrite_Username__c': 'FAKE_EVENTBRITE_USERNAME_2',
                        'Hoopla_Account_Name__c': 'FAKE_ACCOUNT_NAME_2',
                        'ActivatedDate': 'FAKE_SIGNED_DATE_2',
                    },
                ]
            },
        )
        case_numbers = ['FAKE_CASE_NUMBER_1', 'FAKE_CASE_NUMBER_2']
        sfq = _generate_fake_salesforce_query_instance()
        with patch.object(sfq.sf, 'query', side_effect=FAKE_SF_QUERY_RESPONSES), \
                patch.object(SalesforceQuery, '__init__', return_value=None):
            result = sfq.fetch_cases(','.join(case_numbers))
        for elem in result:
            self.assertIn(elem['case_number'], case_numbers)

    def test_fetch_cases_by_date(self):
        FAKE_SF_QUERY_RESPONSES = (
            {
                'records': [
                    {
                        'Id': 'FAKE_CASE_ID_1',
                        'CaseNumber': 'FAKE_CASE_NUMBER_1',
                        'Contract__c': 'FAKE_CONTRACT_ID_1',
                        'Description': 'FAKE_DESCRIPTION_1',
                        'Case_URL__c': 'FAKE_CASE_URL_1',
                    },
                    {
                        'Id': 'FAKE_CASE_ID_2',
                        'CaseNumber': 'FAKE_CASE_NUMBER_2',
                        'Contract__c': 'FAKE_CONTRACT_ID_2',
                        'Description': 'FAKE_DESCRIPTION_2',
                        'Case_URL__c': 'FAKE_CASE_URL_2',
                    },
                 ]
            },
            {
                'records': [
                    {
                        'Id': 'FAKE_CONTRACT_ID_1',
                        'Eventbrite_Username__c': 'FAKE_EVENTBRITE_USERNAME_1',
                        'Hoopla_Account_Name__c': 'FAKE_ACCOUNT_NAME_1',
                        'ActivatedDate': 'FAKE_SIGNED_DATE_1',
                    },
                    {
                        'Id': 'FAKE_CONTRACT_ID_2',
                        'Eventbrite_Username__c': 'FAKE_EVENTBRITE_USERNAME_2',
                        'Hoopla_Account_Name__c': 'FAKE_ACCOUNT_NAME_2',
                        'ActivatedDate': 'FAKE_SIGNED_DATE_2',
                    },
                ]
            },
        )
        dates_from_to = ['FAKE_SIGNED_DATE_FROM_1', 'FAKE_SIGNED_DATE_TO_1']
        case_numbers = ['FAKE_CASE_NUMBER_1', 'FAKE_CASE_NUMBER_2']
        sfq = _generate_fake_salesforce_query_instance()
        with patch.object(sfq.sf, 'query', side_effect=FAKE_SF_QUERY_RESPONSES):
            result = sfq.fetch_cases_by_date(dates_from_to[0], dates_from_to[1])
        for elem in result:
            self.assertIn(elem['case_number'], case_numbers)


class AddContractTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_add_contract_view(self):
        FAKE_CASE_NUMBERS = ['1234', '5678']
        kwargs = {
            'case_numbers': ','.join(FAKE_CASE_NUMBERS),
        }
        request = self.factory.get(reverse('contracts-add'), kwargs=kwargs)
        FAKE_FETCH_DATA = [
            {
                'case_number': FAKE_CASE_NUMBERS[0],
                'case_id': 'FAKE_CASE_ID_1',
                'contract_id': 'FAKE_CASE_CONTRACT_ID_1',
                'organizer_email': 'FAKE_CASE_CONTRACT_USERNAME_1',
                'organizer_name': 'FAKE_CASE_ORGANIZER_NAME_1',
                'signed_date': '2019-02-08T21:26:13.000+0000',
                'link_to_salesforce_case': 'https://pe33.zzxxzzz.com/5348fObs',
            },
            {
                'case_number': FAKE_CASE_NUMBERS[1],
                'case_id': 'FAKE_CASE_NUMBER_2',
                'contract_id': 'FAKE_CASE_CONTRACT_ID_2',
                'organizer_email': 'FAKE_CASE_CONTRACT_USERNAME_2',
                'organizer_name': 'FAKE_CASE_ORGANIZER_NAME_2',
                'signed_date': '2019-02-08T21:26:13.000+0000',
                'link_to_salesforce_case': 'https://pe33.zzxxzzz.com/5348fObs',
            },
        ]
        with patch('app.views.SalesforceQuery.fetch_cases', return_value=FAKE_FETCH_DATA), \
                patch.object(SalesforceQuery, '__init__', return_value=None):
            response = ContractAdd.as_view()(request, **kwargs)
        self.assertEqual(response.status_code, 200)
        response = response.render().content
        for elem in FAKE_FETCH_DATA:
            elem['signed_date'] = '02/08/2019'
            for key, value in elem.items():
                self.assertIn(bytes(value, encoding='utf-8'), response)

    def test_save_case(self):
        FAKE_CASE_ID = 'FAKE_CASE_ID'
        FAKE_CONTRACT_ID = 'FAKE_CONTRACT_ID'
        kwargs = {'contract_id': FAKE_CONTRACT_ID}
        request = self.factory.post(reverse('contracts-save', args=(FAKE_CONTRACT_ID,)), data={'case_id': FAKE_CASE_ID})
        FAKE_CASE_RETURN = {
            'Id': FAKE_CASE_ID,
            'CaseNumber': "FAKE_CASE_NUMBER",
            'Description': "FAKE_CASE_DESCRIPTION",
            'Contract__c': FAKE_CONTRACT_ID,
            'Case_URL__c': 'https://pe33.zzxxzzz.com/5348fObs',
        }
        FAKE_CONTRACT_RETURN = {
            'Hoopla_Account_Name__c': 'FAKE_ORGANIZER_NAME',
            'Eventbrite_Username__c': 'FAKE_ORGANIZER_EMAIL',
            'ActivatedDate': '2019-02-08T21:26:13.000+0000',
        }
        FAKE_ATTACHMENT_RETURN = [{
            'name': 'FAKE_ATTACHMENT_NAME',
            'salesforce_id': 'FAKE_ATTACHMENT_SALESFORCE_ID',
            'content_type': 'FAKE_ATTACHMENT_CONTENT_TYPE',
        }]

        with patch('app.views.SalesforceQuery.get_case_by_id', return_value=FAKE_CASE_RETURN), \
                patch('app.views.SalesforceQuery.get_contract_by_id', return_value=FAKE_CONTRACT_RETURN), \
                patch('app.views.SalesforceQuery.fetch_contract_attachments', return_value=FAKE_ATTACHMENT_RETURN), \
                patch.object(SalesforceQuery, '__init__', return_value=None):
            response = SaveCaseView.as_view()(request, **kwargs)
        self.assertEqual(response.status_code, 302)
        contract = Contract.objects.first()
        self.assertEqual(contract.case_number, FAKE_CASE_RETURN['CaseNumber'])

    def test_get_case_already_persisted(self):
        contract = ContractFactory.create()
        kwargs = {
            'case_numbers': contract.case_number
        }
        request = self.factory.get(reverse('contracts-add'))
        FAKE_FETCH_DATA = [
            {
                'case_number': "428967",
                'case_id': contract.salesforce_case_id,
                'contract_id': 'FAKE_CASE_CONTRACT_ID_1',
                'organizer_email': 'FAKE_CASE_CONTRACT_USERNAME_1',
                'organizer_name': 'FAKE_CASE_ORGANIZER_NAME_1',
                'signed_date': '2019-02-08T21:26:13.000+0000',
                'link_to_salesforce_case': 'https://pe33.zzxxzzz.com/5348fObs',
            },
        ]
        with patch('app.views.SalesforceQuery.fetch_cases', return_value=FAKE_FETCH_DATA), \
                patch.object(SalesforceQuery, '__init__', return_value=None):
            response = ContractAdd.as_view()(request, **kwargs)
        response = response.render().content
        self.assertIn(bytes("This contract already exists.", encoding='utf-8'), response)


class InstallmentTest(TestCase):

    def test_create_installment_table(self):
        factory = RequestFactory()
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
        }
        contract = Contract.objects.create(**contract_data)
        installment_data = {
            'contract': contract,
            'is_recoup': False,
            'status': 'PENDING',
            'upfront_projection': 19000,
            'recoup_amount': 14000,
            'maximum_payment_date': '2019-09-14',
            'payment_date': '2019-09-10',
            'gtf': 3500,
            'gts': 10000,
        }
        Installment.objects.create(**installment_data)
        kwargs = {'contract_id': contract.id}
        url = reverse('installments-create', kwargs=kwargs)
        request = factory.get(url)
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        response = InstallmentView.as_view()(request, **kwargs)
        content = response.render().content
        self.assertIn(bytes(contract_data['organizer_email'], encoding='utf-8'), content)

    def test_update_installment(self):
        factory = RequestFactory()
        installment = InstallmentFactory()
        installment_data = installment.__dict__
        installment_data['is_recoup'] = True
        installment_data['payment_date'] = datetime.date(2018, 3, 2)
        installment_data['maximum_payment_date'] = datetime.date(2018, 7, 1)
        installment_data['recoup_amount'] = 9999
        kwargs = {
            'contract_id': installment.contract_id,
            'pk': installment.id,
        }
        request = factory.post(
            reverse('installments-update', kwargs=kwargs),
            installment_data,
        )
        InstallmentUpdate.as_view()(request, **kwargs)
        installment_updated = Installment.objects.first()
        self.assertEqual(installment_data['is_recoup'], installment_updated.is_recoup)
        self.assertEqual(installment_data['payment_date'], installment_updated.payment_date)
        self.assertEqual(installment_data['maximum_payment_date'], installment_updated.maximum_payment_date)
        self.assertEqual(installment_data['recoup_amount'], installment_updated.recoup_amount)

    def test_delete_installment(self):
        factory = RequestFactory()
        installment = InstallmentFactory()
        kwargs = {
            'contract_id': installment.contract_id,
            'pk': installment.id,
        }
        request = factory.post(
            reverse('installments-delete', kwargs=kwargs)
        )
        InstallmentDelete.as_view()(request, **kwargs)
        self.assertEqual(None, Installment.objects.first())

    def test_calculate_balance(self):
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
        }
        contract = Contract.objects.create(**contract_data)
        installment_data = {
            'contract': contract,
            'is_recoup': False,
            'status': 'PENDING',
            'upfront_projection': 19000,
            'recoup_amount': 14000,
            'maximum_payment_date': '2019-09-14',
            'payment_date': '2019-09-10',
            'gtf': 3500,
            'gts': 10000,
        }
        calculated_balance = installment_data['upfront_projection'] - installment_data['recoup_amount']
        installment1 = Installment.objects.create(**installment_data)
        self.assertEqual(calculated_balance, installment1.balance)

    def test_balance_with_empty_installment_fields(self):
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
        }
        contract = Contract.objects.create(**contract_data)
        installment_data = {
            'contract': contract,
            'is_recoup': False,
        }
        installment = Installment.objects.create(**installment_data)
        self.assertEqual(0, installment.balance)
        installment_data['upfront_projection'] = 1234
        installment1 = Installment.objects.create(**installment_data)
        self.assertEqual(installment_data['upfront_projection'], installment1.balance)


class AllInstallmentsViewTest(TestCase):

    def setUp(self):
        contract1 = Contract.objects.create(
            organizer_account_name='EDA',
            organizer_email='test@test.com',
            signed_date='2019-03-20',
            description='Some description',
            case_number='903847iuew',
            salesforce_id='4230789sdfk',
            salesforce_case_id='4237sdfk423',
        )
        contract2 = Contract.objects.create(
            organizer_account_name='NOT_AN_INTERESTING_NAME',
            organizer_email='test@test.com',
            signed_date='2019-03-15',
            description='Other description',
            case_number='089i3e423w',
            salesforce_id='98773hsj',
            salesforce_case_id='sasdfk42g3',
        )
        contract3 = Contract.objects.create(
            organizer_account_name='NOT_AN_INTERESTING_NAME',
            organizer_email='test@eda.com',
            signed_date='2019-03-15',
            description='This is important contract information',
            case_number='1234asd',
            salesforce_id='fks02934',
            salesforce_case_id='534798vbk',
        )
        self.installment1 = Installment.objects.create(
            contract=contract1,
            is_recoup=True,
            status='COMMITED/APPROVED',
            upfront_projection=77777,
            maximum_payment_date='2019-05-30',
            payment_date='2019-05-05',
            recoup_amount=55555,
            gtf=100000,
            gts=7000,
        )
        self.installment2 = Installment.objects.create(
            contract=contract2,
            is_recoup=True,
            status='COMMITED/APPROVED',
            upfront_projection=587934,
            maximum_payment_date='2019-05-30',
            payment_date='2019-05-25',
            recoup_amount=98736,
            gtf=6280,
            gts=1830,
        )
        self.installment3 = Installment.objects.create(
            contract=contract3,
            is_recoup=False,
            status='PENDING',
            upfront_projection=77777,
            maximum_payment_date='2019-05-30',
            payment_date='2019-05-05',
            recoup_amount=55555,
            gtf=100000,
            gts=7000,
        )

    def test_all_installments_view(self):

        '''Test "AllInstallmentsView". In this view all installments are shown.'''

        factory = RequestFactory()

        request = factory.get(reverse('all-installments'))
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        response = AllInstallmentsView.as_view()(request)
        self.assertIn(
            bytes(self.installment1.status, encoding='utf-8'), response.render().content
        )
        self.assertIn(
            bytes(str(intcomma(self.installment2.gtf)), encoding='utf-8'), response.render().content
        )
        self.assertIn(
            bytes(str(intcomma(self.installment3.upfront_projection)), encoding='utf-8'), response.render().content
        )

    def test_filter_installment(self):
        qs = Installment.objects.all()
        f = InstallmentsFilter()
        result_search_status = f.search_status(qs, '', 'COMMITED/APPROVED')
        result_search_organizer = f.search_contract_organizer(qs, '', 'EDA')
        result_search_signed_date = f.search_contract_signed_date(qs, '', '2019-03-15')
        result_search_maximum_payment_date = f.search_maximum_payment_date(qs, '', '2019-05-30')
        result_search_payment_date = f.search_payment_date(qs, '', '2019-05-05')
        self.assertIn(self.installment1, result_search_status)
        self.assertIn(self.installment1, result_search_organizer)
        self.assertIn(self.installment2, result_search_status)
        self.assertIn(self.installment2, result_search_signed_date)
        self.assertNotIn(self.installment2, result_search_payment_date)
        self.assertIn(self.installment3, result_search_maximum_payment_date)
        self.assertIn(self.installment3, result_search_payment_date)
        self.assertNotIn(self.installment3, result_search_status)

    def test_all_installments_pagination_incomplete_page(self):

        factory = RequestFactory()

        request = factory.get(reverse('all-installments'))
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        response = AllInstallmentsView.as_view()(request)
        expected_number_of_elements_in_first_page = 3
        self.assertEqual(expected_number_of_elements_in_first_page, len(response.context_data['object_list']))
        self.assertFalse(response.context_data['is_paginated'])

    def test_all_installments_pagination_complete_page(self):

        factory = RequestFactory()

        contract = ContractFactory()
        items_per_page_exceed = ITEMS_PER_PAGE + 1
        InstallmentFactory.create_batch(items_per_page_exceed, contract=contract)

        request = factory.get(reverse('all-installments'))
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        response = AllInstallmentsView.as_view()(request)
        expected_number_of_elements_in_a_full_first_page = ITEMS_PER_PAGE
        self.assertEqual(expected_number_of_elements_in_a_full_first_page, len(response.context_data['object_list']))
        self.assertTrue(response.context_data['is_paginated'])


class UploadBackUpFilesTest(TestCase):

    def setUp(self):
        self.file_mock = MagicMock(spec=File)
        self.file_mock = mock.MagicMock(spec=File, name='FileMock')
        self.file_mock.name = 'test.pdf'

    @mock.patch('django.core.files.storage.default_storage._wrapped')
    def test_save_file(self, storage_mock):
        self.file_mock = mock.MagicMock(spec=File, name='FileMock')
        self.file_mock.name = 'test.pdf'
        condition_file = InstallmentConditionFactory.create()
        condition_file.upload_file = self.file_mock

        condition_file.save()

        self.assertIsNotNone(condition_file.upload_file)

    @mock.patch('django.core.files.storage.default_storage._wrapped')
    def test_render_view_with_file(self, storage_mock):
        self.file_mock = mock.MagicMock(spec=File, name='FileMock')
        self.file_mock.name = 'test.pdf'
        condition_file = InstallmentConditionFactory.create()
        condition_file.upload_file = self.file_mock

        condition_file.save()
        factory = RequestFactory()
        kwargs = {
            'contract_id': condition_file.installment.contract_id,
            'installment_id': condition_file.installment.id,
            'condition_id': condition_file.id,
        }
        request = factory.post(
            reverse('condition_backup_proof', kwargs=kwargs)
        )
        response = ConditionBackupProofView.as_view()(request, **kwargs)
        kwargs_response = {
            'contract_id': condition_file.installment.contract_id,
            'installment_id': condition_file.installment.id,
        }

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('conditions', kwargs=kwargs_response))

    @mock.patch('django.core.files.storage.default_storage._wrapped')
    def test_delete_file_uploaded(self, storage_mock):
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.jpg'
        condition = InstallmentConditionFactory.create()
        condition.upload_file = file_mock
        condition.save()
        factory = RequestFactory()
        kwargs = {
            'contract_id': condition.installment.contract_id,
            'installment_id': condition.installment.id,
            'condition_id': condition.id,
        }
        request = factory.post(
            reverse('delete-uploaded-file', kwargs=kwargs)
        )
        with mock.patch.object(InstallmentCondition, 'delete_upload_file'):
            response = DeleteUploadedFileCondition.as_view()(request, **kwargs)
        self.assertEqual(response.status_code, 302)


class PrestoQueriesTest(TestCase):
    def test_generate_presto_query(self):
        event_id = '1234'
        from_date = datetime.date(2019, 3, 8)
        to_date = datetime.date(2019, 5, 8)
        expected_query = dedent("""
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
                AND f.currency IN ('BRL')
                AND trx_date > '{from_date}'
                AND trx_date < '{to_date}'
                AND f.event_id = {event_id}

        GROUP BY 1,2,3,4
        """).format(
            from_date=from_date.strftime(SUPERSET_QUERY_DATE_FORMAT),
            to_date=to_date.strftime(SUPERSET_QUERY_DATE_FORMAT),
            event_id=event_id,
        )

        result = generate_presto_query(event_id, from_date, to_date)

        self.assertEqual(expected_query, result)

    def test_ajax_presto_query_endpoint(self):
        client = Client()
        EVENT_ID = '1234'
        FROM_DATE = '2019-10-24'
        TO_DATE = '2019-11-24'

        response = client.get(
            reverse('superset_query'),
            {
                'event-id': EVENT_ID,
                'from-date': FROM_DATE,
                'to-date': TO_DATE,
            }
        )

        self.assertEqual(
            response.json()['query'],
            generate_presto_query(
                EVENT_ID,
                datetime.datetime.strptime(FROM_DATE, SUPERSET_QUERY_DATE_FORMAT),
                datetime.datetime.strptime(TO_DATE, SUPERSET_QUERY_DATE_FORMAT),
            )
        )


class DownloadAttachment(TestCase):

    def test_get_one_contract_attachment(self):
        FAKE_ATTACHMENT_ID = 'FAKE_ATTACHMENT_ID_1'
        FAKE_SF_QUERY_RESPONSES = (
            {
                'records': [
                    {
                        'Id': 'FAKE_ATTACHMENT_ID_1',
                        'Name': 'FAKE_NAME_1',
                        'ContentType': 'FAKE_CONTENT_TYPE_1',
                    },
                 ]
            },
        )
        contract_id = ['FAKE_CONTRACT_ID_1']
        sfq = _generate_fake_salesforce_query_instance()
        with patch.object(sfq.sf, 'query', side_effect=FAKE_SF_QUERY_RESPONSES):
            result = sfq.fetch_contract_attachments(contract_id)
        for attachment in result:
            self.assertEqual(attachment['salesforce_id'], FAKE_ATTACHMENT_ID)

    def test_get_contract_attachments(self):
        FAKE_ATTACHMENT_ID = ['FAKE_ATTACHMENT_ID_1', 'FAKE_ATTACHMENT_ID_2']
        FAKE_SF_QUERY_RESPONSES = (
            {
                'records': [
                    {
                        'Id': 'FAKE_ATTACHMENT_ID_1',
                        'Name': 'FAKE_NAME_1',
                        'ContentType': 'FAKE_CONTENT_TYPE_1',
                    },
                    {
                        'Id': 'FAKE_ATTACHMENT_ID_2',
                        'Name': 'FAKE_NAME_2',
                        'ContentType': 'FAKE_CONTENT_TYPE_2',
                    },
                 ]
            },
        )
        contract_id = ['FAKE_CONTRACT_ID_1']
        sfq = _generate_fake_salesforce_query_instance()
        with patch.object(sfq.sf, 'query', side_effect=FAKE_SF_QUERY_RESPONSES):
            result = sfq.fetch_contract_attachments(contract_id)
        for attachment in result:
            self.assertIn(attachment['salesforce_id'], FAKE_ATTACHMENT_ID)

    def test_fetch_attachment(self):
        FAKE_BODY = base64.b64encode(b"FAKE_CONTRACT_BODY")
        FAKE_CONTENT_TYPE = "FAKE_CONTENT_TYPE"
        FAKE_ATTACHMENT_ID = "FAKE_ATTACHMENT_ID"
        sfq = _generate_fake_salesforce_query_instance()

        with patch.object(requests, 'get', return_value=FAKE_BODY):
            response = sfq.fetch_attachment(FAKE_ATTACHMENT_ID, FAKE_CONTENT_TYPE)

        self.assertEqual(response, FAKE_BODY)

    def test_download_attachment(self):
        client = Client()
        attachment = AttachmentFactory()
        kwargs = {
            'attachment_id': attachment.id,
        }
        FAKE_BODY = base64.b64encode(b"FAKE_CONTRACT_BODY")
        attachment_mock = Mock()
        attachment_mock.content = FAKE_BODY

        with patch.object(SalesforceQuery, 'fetch_attachment', return_value=attachment_mock), \
                patch.object(SalesforceQuery, '__init__', return_value=None):
            response = client.get(
                reverse('download_attachment', kwargs=kwargs),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, FAKE_BODY)

    def test_render_attachment_in_installment_viewg(self):
        factory = RequestFactory()
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
        }
        contract = Contract.objects.create(**contract_data)
        attachment = AttachmentFactory()
        attachment.contract = contract
        attachment.save()
        kwargs = {'contract_id': contract.id}
        url = reverse('installments-create', kwargs=kwargs)
        request = factory.get(url)
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        response = InstallmentView.as_view()(request, **kwargs)
        content = response.render().content
        self.assertIn(bytes(attachment.name, encoding='utf-8'), content)


class DetailContractTest(TestCase):

    def test_detail_contract(self):
        contract = ContractFactory()
        event = Event.objects.create(
            event_name="Festival",
            event_id="8523iuw98",
            contract=contract,
        )
        factory = RequestFactory()
        kwargs = {'pk': contract.id}
        request = factory.get(reverse('contracts-detail', args=[contract.id]))
        response = DetailContractView.as_view()(request, **kwargs)
        resp = response.render()
        self.assertIn(bytes(contract.organizer_email, encoding='utf-8'), resp.content)
        self.assertIn(bytes(contract.organizer_account_name, encoding='utf-8'), resp.content)
        self.assertIn(bytes(event.event_name, encoding='utf-8'), resp.content)


class CreateEventTest(TestCase):

    def test_create_event(self):
        contract = ContractFactory()
        factory = RequestFactory()
        kwargs = {'contract_id': contract.id}
        event_data = {
            'Event Name': 'Festival',
            'Event id': '235fj35a',
            'Contract': contract,
        }
        request = factory.post(reverse('events-create', args=[contract.id]), event_data)
        CreateEvent.as_view()(request, **kwargs)
        event = contract.events.all().get()
        self.assertEqual(event_data['Event id'], event.event_id)
        self.assertEqual(event_data['Event Name'], event.event_name)


class DeleteEventTest(TestCase):

    def test_delete_event(self):
        factory = RequestFactory()
        event = EventFactory()
        kwargs = {
            'contract_id': event.contract_id,
            'event_id': event.id,
        }
        request = factory.post(reverse('events-delete', args=[event.contract_id, event.id]))
        DeleteEvent.as_view()(request, **kwargs)
        event_query = Event.objects.filter(id=event.id)
        self.assertEqual(event_query.count(), 0)


class TestUserForm(TestCase):

    def test_forms(self):
        User.objects.create_user(
            username='test', email='test@test.com', password='Secret123')
        form_data = {
            'username': 'test',
            'password': 'Secret123',
        }
        form = CustomAuthenticationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        Error = 'Please enter a correct username and password. Note that both fields may be case-sensitive.'
        User.objects.create_user(
            username='test', email='test@test.com', password='Secret123')
        form_data = {
            'username': 'test',
            'password': 'secret123',
        }
        form = CustomAuthenticationForm(data=form_data)
        self.assertEqual(form.errors['__all__'][0], Error)
