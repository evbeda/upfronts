import datetime
from django.db import models

from . import (
    STATUS,
)


class Contract(models.Model):
    organizer_account_name = models.CharField(max_length=80)
    organizer_email = models.EmailField()
    signed_date = models.DateField()
    event_id = models.CharField(max_length=80, null=True, blank=True)
    user_id = models.CharField(max_length=80, null=True, blank=True)
    description = models.TextField()
    case_number = models.CharField(max_length=80, unique=True)
    salesforce_id = models.CharField(max_length=80)
    salesforce_case_id = models.CharField(max_length=80)
    link_to_salesforce_case = models.CharField(max_length=40)

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
    def balance(self):
        return self.upfront_projection - self.recoup_amount

    @property
    def conditions(self):
        return self

    @property
    def delete(self):
        return self

    @property
    def edit(self):
        return self


class InstallmentCondition(models.Model):
    condition_name = models.CharField(max_length=80)
    installment = models.ForeignKey(Installment, on_delete=models.CASCADE)
    done = models.DateTimeField(blank=True, null=True)

    def toggle_done(self):
        self.done = None if self.done else datetime.datetime.now()
        self.save()


class Attachment(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    salesforce_id = models.CharField(max_length=40)
    name = models.CharField(max_length=80)
    content_type = models.CharField(max_length=40)
