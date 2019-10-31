# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-10-31 13:50
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organizer_account_name', models.CharField(max_length=80)),
                ('organizer_email', models.EmailField(max_length=254)),
                ('signed_date', models.DateField()),
                ('event_id', models.CharField(blank=True, max_length=80, null=True)),
                ('user_id', models.CharField(blank=True, max_length=80, null=True)),
                ('description', models.TextField()),
                ('case_number', models.CharField(max_length=80, unique=True)),
                ('salesforce_id', models.CharField(max_length=80)),
                ('salesforce_case_id', models.CharField(max_length=80)),
                ('link_to_salesforce_case', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='Installment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_recoup', models.BooleanField()),
                ('status', models.CharField(choices=[('COMMITED/APPROVED', 'COMMITED/APPROVED'), ('PENDING', 'PENDING')], max_length=80)),
                ('upfront_projection', models.DecimalField(decimal_places=4, max_digits=19)),
                ('maximum_payment_date', models.DateField()),
                ('payment_date', models.DateField()),
                ('recoup_amount', models.DecimalField(decimal_places=4, max_digits=19)),
                ('gtf', models.DecimalField(decimal_places=4, max_digits=19)),
                ('gts', models.DecimalField(decimal_places=4, max_digits=19)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Contract')),
            ],
        ),
        migrations.CreateModel(
            name='InstallmentCondition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condition_name', models.CharField(max_length=80)),
                ('done', models.DateTimeField(blank=True, null=True)),
                ('upload_file', models.FileField(blank=True, upload_to='', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'xls', 'png', 'jpeg', 'jpg'])])),
                ('installment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Installment')),
            ],
        ),
    ]
