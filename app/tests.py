from django.core.exceptions import ValidationError
from django.test import TestCase
from .models import Contract, Installment, InstallmentCondition
from . import \
    INVALID_SIGN_DATE,\
    INVALID_PAYMENT_DATE,\
    INVALID_RECOUP_AMOUNT,\
    STATUS,\
    INSTALLMENT_CONDITIONS


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
        self.contract = Contract(**contract_data)
        self.contract.save()

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


    # def test_create_invalid_installment_condition(self):
    #     installment_condition_data = {
    #         'installment': self.installment,
    #         'done': False,
    #     }
    #     installment_condition = InstallmentCondition(**installment_condition_data)
    #     installment_condition.full_clean()


# #
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
