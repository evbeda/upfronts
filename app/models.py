from django.db import models

from . import (
    INSTALLMENT_CONDITIONS,
    STATUS,
)


class Contract(models.Model):
    organizer_account_name = models.CharField(max_length=80)
    organizer_email = models.EmailField()
    signed_date = models.DateField()
    event_id = models.CharField(max_length=80, null=True, blank=True)
    user_id = models.CharField(max_length=80, null=True, blank=True)

    @property
    def edit(self):
        return self

    @property
    def installments(self):
        return self


class Installment(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    is_recoup = models.BooleanField()
    status = models.CharField(max_length=80, choices=STATUS)
    upfront_projection = models.DecimalField(max_digits=19, decimal_places=4)
    maximum_payment_date = models.DateField()
    payment_date = models.DateField()
    recoup_amount = models.DecimalField(max_digits=19, decimal_places=4)
    gtf = models.DecimalField(max_digits=19, decimal_places=4)
    gts = models.DecimalField(max_digits=19, decimal_places=4)

    @property
    def edit(self):
        return self


class InstallmentCondition(models.Model):
    condition_name = models.CharField(max_length=80, choices=INSTALLMENT_CONDITIONS)
    installment = models.ForeignKey(Installment, on_delete=models.CASCADE)
    done = models.BooleanField(default=False)
