# Generated by Django 4.2.3 on 2023-09-07 18:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proj', '0039_transaction_delete_mytransaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitemm',
            name='paid_status',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='CartOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_no', models.CharField(max_length=200)),
                ('product_status', models.CharField(choices=[('process', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered')], default='processing', max_length=30)),
                ('cart_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proj.cartitemm')),
            ],
        ),
    ]