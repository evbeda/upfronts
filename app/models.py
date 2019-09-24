from django.db import models
from . import STATUS, INSTALLMENT_CONDITIONS


class Contract(models.Model):
    organizer_account_name = models.CharField(max_length=80)
    organizer_email = models.EmailField()
    signed_date = models.DateField()


class Installment(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    is_recoup = models.BooleanField()
    status = models.CharField(max_length=80, choices=STATUS)
    upfront_projection = models.DecimalField(max_digits=19, decimal_places=10)
    maximum_payment_date = models.DateField()
    payment_date = models.DateField()
    recoup_amount = models.DecimalField(max_digits=19, decimal_places=10)
    gtf = models.DecimalField(max_digits=19, decimal_places=10)
    gts = models.DecimalField(max_digits=19, decimal_places=10)


class InstallmentCondition(models.Model):
    condition_name = models.CharField(max_length=80, choices=INSTALLMENT_CONDITIONS)
    installment = models.ForeignKey(Installment, on_delete=models.CASCADE)
    done = models.BooleanField(default=False)


# class Upfront(models.Model):
#     is_recoup = models.BooleanField()
#     status = models.CharField(max_length=80, choices=STATUS)
#     organizer = models.CharField(max_length=80)
#     account_name = models.CharField(max_length=80)
#     email_organizer = models.EmailField()
#     upfront_projection = models.DecimalField(max_digits=19, decimal_places=10)
#     contract_signed_date = models.DateField()
#     maximum_payment_date = models.DateField()
#     payment_date = models.DateField()
#     recoup_amount = models.DecimalField(max_digits=19, decimal_places=10)
#     gtf = models.DecimalField(max_digits=19, decimal_places=10)
#     gts = models.DecimalField(max_digits=19, decimal_places=10)
