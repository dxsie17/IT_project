from django.contrib import admin

# Register your models here.
from .models import Merchant, Category, Item

admin.site.register(Merchant)
admin.site.register(Category)
admin.site.register(Item)
