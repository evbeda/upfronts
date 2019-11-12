import datetime

from django.core.validators import FileExtensionValidator
from django.db import models

from . import (
    STATUS_COMMITED_APPROVED,
    STATUS,
)


class Contract(models.Model):
    organizer_account_name = models.CharField(max_length=80)
    organizer_email = models.EmailField()
    signed_date = models.DateField()
    user_id = models.CharField(max_length=80, null=True, blank=True)
    description = models.TextField()
    case_number = models.CharField(max_length=80, unique=True)
    salesforce_id = models.CharField(max_length=80)
    salesforce_case_id = models.CharField(max_length=80)
    link_to_salesforce_case = models.CharField(max_length=120)

    @property
    def details(self):
        return self

    @property
    def installments(self):
        return self


class Installment(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    is_recoup = models.BooleanField(blank=True)
    status = models.CharField(max_length=80, default=STATUS_COMMITED_APPROVED, choices=STATUS, null=True, blank=True)
    upfront_projection = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Upfront"
    )
    maximum_payment_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    recoup_amount = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    gtf = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True, verbose_name="GTF")
    gts = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True, verbose_name="GTS")

    @property
    def balance(self):
        upfront_projection = self.upfront_projection or 0
        recoup_amount = self.recoup_amount or 0
        return upfront_projection - recoup_amount

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
    done = models.DateTimeField(blank=True, null=True)
    installment = models.ForeignKey(Installment, on_delete=models.CASCADE)
    upload_file = models.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'xls', 'png',  'jpeg', 'jpg'])],
        blank=True,
    )

    def delete_upload_file(self):
        self.upload_file.delete()

    def toggle_done(self):
        self.done = None if self.done else datetime.datetime.now()
        self.save()


class Attachment(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    salesforce_id = models.CharField(max_length=40)
    name = models.CharField(max_length=80)
    content_type = models.CharField(max_length=40)


class Event(models.Model):
    event_id = models.CharField(max_length=40)
    event_name = models.CharField(max_length=40)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='events')
