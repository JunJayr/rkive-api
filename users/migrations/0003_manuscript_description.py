# Generated by Django 5.1.4 on 2025-02-02 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_manuscript'),
    ]

    operations = [
        migrations.AddField(
            model_name='manuscript',
            name='description',
            field=models.TextField(blank=True, help_text='Brief description or abstract of the manuscript'),
        ),
    ]
