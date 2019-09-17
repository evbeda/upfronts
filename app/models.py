from django.db import models


STATUS = [
    ('COMMITED/APPROVED', 'COMMITED/APPROVED'),
    ('PENDING', 'PENDING'),
]


class Upfront(models.Model):
    is_recoup = models.BooleanField()
    status = models.CharField(max_length=80, choices=STATUS)
    organizer = models.CharField(max_length=80)
    account_name = models.CharField(max_length=80)
    email_organizer = models.EmailField()
    upfront_projection = models.DecimalField(max_digits=19, decimal_places=10)
    contract_signed_date = models.DateField()
    maximum_payment_date = models.DateField()
    payment_date = models.DateField()
    recoup_amount = models.DecimalField(max_digits=19, decimal_places=10)
    gtf = models.DecimalField(max_digits=19, decimal_places=10)
    gts = models.DecimalField(max_digits=19, decimal_places=10)
