# Generated by Django 5.1.7 on 2025-03-16 01:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0006_alter_order_order_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="order_number",
            field=models.CharField(default="B3AF3F155C", max_length=20, unique=True),
        ),
    ]
