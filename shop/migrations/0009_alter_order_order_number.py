# Generated by Django 5.1.7 on 2025-03-19 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0008_category_merchant_alter_category_name_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="order_number",
            field=models.CharField(default="A40BDD7406", max_length=20, unique=True),
        ),
    ]
