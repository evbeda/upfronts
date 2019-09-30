import csv
import io

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

from . import (
    INVALID_SIGN_DATE,
    INVALID_PAYMENT_DATE,
    INVALID_RECOUP_AMOUNT,
    INSTALLMENT_CONDITIONS,
    STATUS,
)
from app.views import (
    download_csv,
    InstallmentsFilter,
    InstallmentsTableView,
)
from app.models import (
    Contract,
    Installment,
    InstallmentCondition,
)


class ModelTest(TestCase):

    def test_create_valid_contract(self):
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
        }
        contract = Contract(**contract_data)
        contract.full_clean()
        contract_data.pop('signed_date')
        contract.full_clean()

    def test_create_invalid_contract(self):
        contract_data = {
            'organizer_email': '1234',
            'signed_date': INVALID_SIGN_DATE,
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


class InstallmentTest(TestCase):

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
        contract = Contract(**contract_data)
        contract.save()
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
        self.installment = Installment(**installment_data)
        self.installment.save()

    def test_create_valid_installment_condition(self):
        installment_condition_data = {
            'condition_name': INSTALLMENT_CONDITIONS[1][0],
            'installment': self.installment,
            'done': False,
        }
        installment_condition = InstallmentCondition(**installment_condition_data)
        installment_condition.full_clean()

    def test_create_invalid_installment_condition(self):
        installment_condition_data = {
            'condition_name': 'INVALID CONDITION',
            'installment': self.installment,
            'done': False,
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
            'done': False,
        }
        expected_response = {
            'installment': ['This field cannot be null.'],
        }
        installment_condition = InstallmentCondition(**installment_condition_data)
        with self.assertRaises(ValidationError) as cm:
            installment_condition.full_clean()
        self.assertEqual(expected_response, cm.exception.message_dict)


class RedirectTest(TestCase):

    def test_redirect_to_login_when_login_is_required(self):
        c = Client()
        response = c.get(reverse('installments'))
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
        ins1 = Installment.objects.create(
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
        ins2 = Installment.objects.create(
                contract=contract2,
                is_recoup=True,
                status='COMMITED/APPROVED',
                upfront_projection=77777,
                maximum_payment_date='2019-05-30',
                payment_date='2019-05-05',
                recoup_amount=55555,
                gtf=100000,
                gts=7000,
        )
        ins3 = Installment.objects.create(
                contract=contract3,
                is_recoup=True,
                status='COMMITED/APPROVED',
                upfront_projection=77777,
                maximum_payment_date='2019-05-30',
                payment_date='2019-05-05',
                recoup_amount=55555,
                gtf=100000,
                gts=7000,
        )
        qs = Installment.objects.all()
        f = InstallmentsFilter()
        result = f.search_organizer(qs, '', 'EDA')
        self.assertIn(ins1, result)
        self.assertIn(ins3, result)
        self.assertNotIn(ins2, result)


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
            'done': False,
        }
        self.installment_condition = InstallmentCondition.objects.create(**installment_condition_data)
        request = factory.get('/installments/')
        request.user = User.objects.create_user(
            username='test', email='test@test.com', password='secret')
        response = InstallmentsTableView.as_view()(request)
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
            reverse('installments-update', args=[contract.id]), contract_data, content_type='application/json')
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
