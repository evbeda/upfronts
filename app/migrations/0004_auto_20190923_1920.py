# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-09-23 19:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_installment_contract'),
    ]

    operations = [
        migrations.RenameField(
            model_name='installment',
            old_name='contract',
            new_name='contract_id',
        ),
    ]
