# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-11-11 14:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20191108_1240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='installment',
            name='status',
            field=models.CharField(blank=True, choices=[('COMMITED/APPROVED', 'COMMITED/APPROVED'), ('INVESTED', 'INVESTED')], default='COMMITED/APPROVED', max_length=80, null=True),
        ),
    ]
