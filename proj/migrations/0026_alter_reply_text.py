# Generated by Django 4.2.3 on 2023-08-26 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proj', '0025_reply'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reply',
            name='text',
            field=models.TextField(max_length=160),
        ),
    ]