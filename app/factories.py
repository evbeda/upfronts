from factory import (
    DjangoModelFactory,
    SubFactory,
)

from django.utils import timezone

from . import models


class ContractFactory(DjangoModelFactory):
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


class InstallmentFactory(DjangoModelFactory):
    class Meta:
        model = models.Installment

    contract = SubFactory(ContractFactory)
    is_recoup = False
    status = 'PENDING'
    upfront_projection = 98345
    maximum_payment_date = '2019-09-14'
    payment_date = '2019-09-14'
    recoup_amount = 736372
    gtf = 873456
    gts = 346897


class InstallmentConditionFactory(DjangoModelFactory):
    class Meta:
        model = models.InstallmentCondition

    installment = SubFactory(InstallmentFactory)
    condition_name = "Promissory note"
