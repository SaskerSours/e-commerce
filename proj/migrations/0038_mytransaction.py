# Generated by Django 4.2.3 on 2023-09-04 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proj', '0037_alter_comparedproduct_unique_together_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(max_length=3)),
                ('paid', models.BooleanField(default=False)),
            ],
        ),
    ]
