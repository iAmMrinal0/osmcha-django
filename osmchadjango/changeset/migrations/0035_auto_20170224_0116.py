# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-02-24 01:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0034_suspicionreasons_is_visible'),
    ]

    operations = [
        migrations.AddField(
            model_name='suspicionreasons',
            name='available_to_changeset',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='suspicionreasons',
            name='available_to_feature',
            field=models.BooleanField(default=True),
        ),
    ]
