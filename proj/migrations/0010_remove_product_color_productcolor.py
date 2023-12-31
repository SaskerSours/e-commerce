# Generated by Django 4.2.3 on 2023-08-04 11:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proj', '0009_delete_clothing_delete_color'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='color',
        ),
        migrations.CreateModel(
            name='ProductColor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.CharField(max_length=100)),
                ('product', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='proj.product')),
            ],
        ),
    ]
