# Generated by Django 2.2.3 on 2019-09-28 01:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_concept_cdb'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotatedentity',
            name='manually_created',
            field=models.BooleanField(default=False),
        ),
    ]
