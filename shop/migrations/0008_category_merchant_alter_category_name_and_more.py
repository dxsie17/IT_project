# Generated by Django 5.1.7 on 2025-03-19 21:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0007_remove_category_is_addon_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="merchant",
            field=models.ForeignKey(
                default=5,
                limit_choices_to={"is_merchant": True},
                on_delete=django.db.models.deletion.CASCADE,
                related_name="categories",
                to="shop.userprofile",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="order",
            name="order_number",
            field=models.CharField(default="009CD9C027", max_length=20, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name="category",
            unique_together={("merchant", "name")},
        ),
        migrations.AlterUniqueTogether(
            name="orderitem",
            unique_together={("order", "item")},
        ),
    ]
