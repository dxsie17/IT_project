from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Merchant)
admin.site.register(Category)
admin.site.register(Item)

# 订单管理
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_merchant')
    search_fields = ('user__username',)
    # list_filter = ('status', 'created_at')
    # ordering = ('-created_at',)

# 订单项管理
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity')
    search_fields = ('order__order_number', 'item__name')

# 评论管理
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'rating', 'created_at')
    search_fields = ('user__username', 'item__name')
    list_filter = ('rating', 'created_at')