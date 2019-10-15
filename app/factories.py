import factory
from . import models
from django.utils import timezone


class ContractFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Contract

    organizer_account_name = 'EDA'
    organizer_email = 'test@test.com'
    signed_date = timezone.now()
    description = 'some description'
    case_number = '47238934'
    salesforce_id = '7908235'
    salesforce_case_id = '5324789dsh39'
    link_to_salesforce_case = 'https://pe33.zzxxzzz.com/5348fObs'
