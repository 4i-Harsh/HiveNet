# Generated by Django 5.1.4 on 2025-01-23 03:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('postchat', '0006_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='email',
            field=models.EmailField(blank=True, max_length=254),
        ),
    ]
