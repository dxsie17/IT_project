# Generated by Django 5.1.7 on 2025-03-19 22:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0009_alter_order_order_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="store_slug",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="order_number",
            field=models.CharField(default="D67DFD0266", max_length=20, unique=True),
        ),
    ]
