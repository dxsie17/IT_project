# Generated by Django 5.1.7 on 2025-03-16 01:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0004_remove_order_user_order_customer_order_order_number_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="order_number",
            field=models.CharField(default="8C08F3E904", max_length=20, unique=True),
        ),
    ]
