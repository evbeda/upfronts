# -*- coding: utf-8 -*-
# Generated by Django 1.11.24 on 2019-10-16 18:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20191014_1320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='installmentcondition',
            name='installment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='app.Installment'),
        ),
    ]
