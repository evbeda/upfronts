from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from .models import Contract, Installment
# from .views import UpfrontFilter

class ModelTest(TestCase):

    def setUp(self):
        contract_data = {
            'organizer_account_name': 'Planner Eventos',
            'organizer_email': 'pepe@planner.com',
            'signed_date': '2019-09-14',
        }
        self.contract=Contract(**contract_data)
        self.contract.save()

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
        INVALID_SIGN_DATE = '5678'
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

    def test_create_valid_installment(self):
        installment_data = {
            'contract': self.contract,
            'is_recoup': False,
            'status': 'PENDING',
            'upfront_projection': 9000,
            'maximum_payment_date':'2019-09-14',
            'payment_date':'2019-09-10',
            'recoup_amount': 14000,
            'gtf': 3500,
            'gts':10000,
        }
        installment = Installment(**installment_data)
        installment.full_clean()

    def test_create_invalid_installment(self):
        INVALID_RECOUP_AMOUNT = '1234A'
        INVALID_PAYMENT_DATE = '28 DE OCTUBRE'
        installment_data = {
            'is_recoup': False,
            'upfront_projection': 9000,
            'maximum_payment_date': INVALID_PAYMENT_DATE,
            'payment_date': '2019-09-10',
            'recoup_amount': INVALID_RECOUP_AMOUNT,
            'gts': 10000,
        }
        expected_error_dict_messages={
            'contract': ['This field cannot be null.'],
            'status': ['This field cannot be blank.'],
            'maximum_payment_date': ["'{}' value has an invalid date format. It must be in YYYY-MM-DD format.".format(INVALID_PAYMENT_DATE)],
            'recoup_amount': ["'{}' value must be a decimal number.".format(INVALID_RECOUP_AMOUNT)],
            'gtf': ['This field cannot be null.'],
        }
        installment = Installment(**installment_data)
        with self.assertRaises(ValidationError) as cm:
            installment.full_clean()
        self.assertEqual(expected_error_dict_messages, cm.exception.message_dict)

#
#
# class RedirectTest(TestCase):
#
#     def test_redirect_to_login_when_login_is_required(self):
#         c = Client()
#         response = c.get("/upfronts/")
#         self.assertIn(reverse('login'), response.url)
#
#
# class FilterTest(TestCase):
#
#     def test_filter_text(self):
#         up1 = Upfront.objects.create(
#                 is_recoup=True,
#                 status='COMMITED/APPROVED',
#                 organizer='EDA',
#                 account_name='AgustinD',
#                 email_organizer='agustin@eventbrite.com',
#                 upfront_projection=77777,
#                 contract_signed_date='2019-04-04',
#                 maximum_payment_date='2019-05-30',
#                 payment_date='2019-05-05',
#                 recoup_amount=55555,
#                 gtf=100000,
#                 gts=7000,
#         )
#         up2 = Upfront.objects.create(
#                 is_recoup=True,
#                 status='COMMITED/APPROVED',
#                 organizer='IDO',
#                 account_name='EDA',
#                 email_organizer='JuanPablo@eventbrite.com',
#                 upfront_projection=77777,
#                 contract_signed_date='2019-04-04',
#                 maximum_payment_date='2019-05-30',
#                 payment_date='2019-05-05',
#                 recoup_amount=55555,
#                 gtf=100000,
#                 gts=7000,
#         )
#         up3 = Upfront.objects.create(
#                 is_recoup=True,
#                 status='COMMITED/APPROVED',
#                 organizer='Me',
#                 account_name='Bucolo',
#                 email_organizer='Walter@eventbrite.com',
#                 upfront_projection=77777,
#                 contract_signed_date='2019-04-04',
#                 maximum_payment_date='2019-05-30',
#                 payment_date='2019-05-05',
#                 recoup_amount=55555,
#                 gtf=100000,
#                 gts=7000,
#         )
#         qs = Upfront.objects.all()
#         f = UpfrontFilter()
#         result = f.search_organizer(qs, '', 'EDA')
#         self.assertIn(up1, result)
#         self.assertIn(up2, result)
#         self.assertNotIn(up3, result)
