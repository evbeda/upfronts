# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-10-10 14:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_auto_20191009_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='link_to_salesforce_case',
            field=models.CharField(default='https://na33.salesforce.com/5003900002GiObs', max_length=40),
            preserve_default=False,
        ),
    ]