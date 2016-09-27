# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-26 19:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('profiles', '0008_change_num_security_questions_default'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('userprofile_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='profiles.UserProfile')),
                ('clinic_code', models.CharField(blank=True, max_length=6, null=True)),
            ],
            options={
                'default_related_name': 'for_nurseconnect',
            },
            bases=('profiles.userprofile',),
        ),
    ]