import csv
import datetime
import io
from unittest.mock import patch

from django.contrib.auth.models import (
    AnonymousUser,
    User,
)
from django.core.exceptions import ValidationError
from django.test import (
    Client,
    RequestFactory,
    TestCase,
)
from django.urls import reverse
from freezegun import freeze_time
from simple_salesforce import Salesforce

from . import (
    INVALID_SIGN_DATE,
    INVALID_PAYMENT_DATE,
    INVALID_RECOUP_AMOUNT,
    INSTALLMENT_CONDITIONS,
    STATUS,
)
from app.views import (
    AllInstallmentsView,
    ContractAdd,
    ContractsFilter,
    ContractsTableView,
    download_csv,
    InstallmentsFilter,
    InstallmentView,
    SaveCaseView,
)
from app.models import (
    Contract,
    Installment,
    InstallmentCondition,
)
from app.utils import fetch_cases


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
            'status': ['This field cannot be blank.'],
            'maximum_payment_date': [
                "'{}' value has an invalid date format. It must be in YYYY-MM-DD format.".format(INVALID_PAYMENT_DATE)],
            'recoup_amount': ["'{}' value must be a decimal number.".format(INVALID_RECOUP_AMOUNT)],
            'gtf': ['This field cannot be null.'],
        }
        installment = Installment(**installment_data)
        with self.assertRaises(ValidationError) as cm:
            installment.full_clean()
        self.assertEqual(expected_error_dict_messages, cm.exception.message_dict)


class InstallmentConditionTest(TestCase):

    def setUp(self):
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

    def test_create_valid_installment_condition(self):
        installment_condition_data = {
            'condition_name': INSTALLMENT_CONDITIONS[1][0],
            'installment': self.installment,
        }
        installment_condition = InstallmentCondition(**installment_condition_data)
        installment_condition.full_clean()

    def test_create_invalid_installment_condition(self):
        installment_condition_data = {
            'condition_name': 'INVALID CONDITION',
            'installment': self.installment,
        }
        expected_response = {
            'condition_name': ["Value 'INVALID CONDITION' is not a valid choice."],
        }
        installment_condition = InstallmentCondition(**installment_condition_data)
        with self.assertRaises(ValidationError) as cm:
            installment_condition.full_clean()
        self.assertEqual(expected_response, cm.exception.message_dict)

    def test_create_installment_condition_without_installment(self):
        installment_condition_data = {
            'condition_name': INSTALLMENT_CONDITIONS[1][0],
        }
        expected_response = {
            'installment': ['This field cannot be null.'],
        }
        installment_condition = InstallmentCondition(**installment_condition_data)
        with self.assertRaises(ValidationError) as cm:
            installment_condition.full_clean()
        self.assertEqual(expected_response, cm.exception.message_dict)

    def test_mark_condition_as_done(self):
        FREEZED_TIME = datetime.datetime(year=2019, month=8, day=20, hour=16, minute=30)
        condition_data = {
            'condition_name': 'TEST_CONDITION_NAME',
            'installment': self.installment,
        }
        condition = InstallmentCondition.objects.create(**condition_data)
        self.assertEqual(condition.done, None)
        with freeze_time(FREEZED_TIME):
            condition.mark_as_done()
        self.assertEqual(condition.done, FREEZED_TIME)


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
        )
        contract2 = Contract.objects.create(
            organizer_account_name='NOT_AN_INTERESTING_NAME',
            organizer_email='test@test.com',
            signed_date='2019-03-15',
        )
        contract3 = Contract.objects.create(
            organizer_account_name='NOT_AN_INTERESTING_NAME',
            organizer_email='test@eda.com',
            signed_date='2019-03-15',
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
            'condition_name': INSTALLMENT_CONDITIONS[1][0],
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
        contract_data['event_id'] = '234523'
        request = factory.post(
            reverse('contracts-update', args=[contract.id]), contract_data, content_type='application/json')
        self.assertIn(bytes(contract_data['event_id'], encoding='utf-8'), request.body)


class TestDownloadCsv(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_status_code_200(self):
        request = self.factory.get(reverse('download_csv'))
        request.user = AnonymousUser()
        response = download_csv(request)
        self.assertEqual(response.status_code, 200)

    def test_download_csv(self):
        request = self.factory.get(reverse('download_csv'))
        request.user = AnonymousUser()
        response = download_csv(request)

        self.assertEqual('text/csv', dict(response.items())['Content-Type'])
        self.assertIn('-upfronts.csv', dict(response.items())['Content-Disposition'])

    def test_download_csv_with_info(self):
        expected_upfront_dict = {
            'is_recoup': 'True',
            'status': 'COMMITED/APPROVED',
            'account_name': 'EDA',
            'email_organizer': 'juan@eventbrite.com',
            'upfront_projection': '77777.0000',
            'contract_signed_date': '2019-04-04',
            'maximum_payment_date': '2019-05-30',
            'payment_date': '2019-05-05',
            'recoup_amount': '55555.0000',
            'gtf': '7000.0000',
            'gts': '100000.0000',
        }
        contract = Contract.objects.create(
            organizer_account_name='EDA',
            organizer_email='juan@eventbrite.com',
            signed_date='2019-04-04',
        )
        Installment.objects.create(
            contract=contract,
            is_recoup=True,
            status='COMMITED/APPROVED',
            upfront_projection=77777,
            maximum_payment_date='2019-05-30',
            payment_date='2019-05-05',
            recoup_amount=55555,
            gtf=100000,
            gts=7000,
        )
        request = self.factory.get(reverse('download_csv'))
        request.user = AnonymousUser()
        response = download_csv(request)
        response_decode = response.content.decode('utf-8')
        csv_list = csv.reader(io.StringIO(response_decode))
        for row in csv_list:
            csv_set = set(row)
        expected_csv_set = set(list(expected_upfront_dict.values()))
        self.assertEqual(csv_set, expected_csv_set)


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
                    },
                    {
                        'Id': 'FAKE_CASE_ID_2',
                        'CaseNumber': 'FAKE_CASE_NUMBER_2',
                        'Contract__c': 'FAKE_CONTRACT_ID_2',
                        'Description': 'FAKE_DESCRIPTION_2',
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
        with patch.object(Salesforce, '__init__', return_value=None), \
                patch.object(Salesforce, 'query', side_effect=FAKE_SF_QUERY_RESPONSES):
            result = fetch_cases(','.join(case_numbers))
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
            },
            {
                'case_number': FAKE_CASE_NUMBERS[1],
                'case_id': 'FAKE_CASE_NUMBER_2',
                'contract_id': 'FAKE_CASE_CONTRACT_ID_2',
                'organizer_email': 'FAKE_CASE_CONTRACT_USERNAME_2',
                'organizer_name': 'FAKE_CASE_ORGANIZER_NAME_2',
                'signed_date': '2019-02-08T21:26:13.000+0000',
            },
        ]
        with patch('app.views.fetch_cases', return_value=FAKE_FETCH_DATA):
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
        }
        FAKE_CONTRACT_RETURN = {
            'Hoopla_Account_Name__c': 'FAKE_ORGANIZER_NAME',
            'Eventbrite_Username__c': 'FAKE_ORGANIZER_EMAIL',
            'ActivatedDate': '2019-02-08T21:26:13.000+0000',
        }

        with patch('app.views.get_case_by_id', return_value=FAKE_CASE_RETURN), \
                patch('app.views.get_contract_by_id', return_value=FAKE_CONTRACT_RETURN):
            response = SaveCaseView.as_view()(request, **kwargs)

        self.assertEqual(response.status_code, 302)
        contract = Contract.objects.first()
        self.assertEqual(contract.case_number, FAKE_CASE_RETURN['CaseNumber'])


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
            'upfront_projection': 9000,
            'maximum_payment_date': '2019-09-14',
            'payment_date': '2019-09-10',
            'recoup_amount': 14000,
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


class AllInstallmentsViewTest(TestCase):

    def test_all_installments_view(self):

        '''Test "AllInstallmentsView". In this view all installments are shown.'''

        factory = RequestFactory()
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
        installment1 = Installment.objects.create(
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
        installment2 = Installment.objects.create(
            contract=contract2,
            is_recoup=True,
            status='COMMITED/APPROVED',
            upfront_projection=587934,
            maximum_payment_date='2019-05-30',
            payment_date='2019-05-05',
            recoup_amount=98736,
            gtf=6280,
            gts=1830,
        )
        installment3 = Installment.objects.create(
            contract=contract3,
            is_recoup=False,
            status='COMMITED/APPROVED',
            upfront_projection=77777,
            maximum_payment_date='2019-05-30',
            payment_date='2019-05-05',
            recoup_amount=55555,
            gtf=100000,
            gts=7000,
        )
        request = factory.get(reverse('all-installments'))
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        response = AllInstallmentsView.as_view()(request)
        self.assertIn(bytes(installment1.status, encoding='utf-8'), response.render().content)
        self.assertIn(bytes(str(installment2.gtf), encoding='utf-8'), response.render().content)
        self.assertIn(bytes(str(installment3.upfront_projection), encoding='utf-8'), response.render().content)

    def test_filter_installment(self):
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
            signed_date='2019-03-16',
            description='This is important contract information',
            case_number='1234asd',
            salesforce_id='fks02934',
            salesforce_case_id='534798vbk',
        )
        installment1 = Installment.objects.create(
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
        installment2 = Installment.objects.create(
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
        installment3 = Installment.objects.create(
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
        qs = Installment.objects.all()
        f = InstallmentsFilter()
        result_search_status = f.search_status(qs, '', 'COMMITED/APPROVED')
        result_search_organizer = f.search_contract_organizer(qs, '', 'EDA')
        result_search_signed_date = f.search_contract_signed_date(qs, '', '2019-03-15')
        result_search_maximum_payment_date = f.search_maximum_payment_date(qs, '', '2019-05-30')
        result_search_payment_date = f.search_payment_date(qs, '', '2019-05-05')
        self.assertIn(installment1, result_search_status)
        self.assertIn(installment1, result_search_organizer)
        self.assertIn(installment2, result_search_status)
        self.assertIn(installment2, result_search_signed_date)
        self.assertNotIn(installment2, result_search_payment_date)
        self.assertIn(installment3, result_search_maximum_payment_date)
        self.assertIn(installment3, result_search_payment_date)
        self.assertNotIn(installment3, result_search_status)
