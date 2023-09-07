# Generated by Django 4.2.3 on 2023-08-09 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proj', '0016_product_discount_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='discount_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
