# Generated by Django 5.1.2 on 2025-03-16 21:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0007_alter_order_order_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="order_number",
            field=models.CharField(default="6E1C507D61", max_length=20, unique=True),
        ),
    ]
