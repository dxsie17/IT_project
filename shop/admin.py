from django.contrib import admin
from .models import UserProfile, Category, Item, Order, OrderItem, Review

# User management (including merchants)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_merchant', 'store_name', 'created_at')
    search_fields = ('user__username', 'store_name')
    list_filter = ('is_merchant',)

# Category management
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ()

# Item management
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_merchant_name', 'category', 'price', 'is_available')
    search_fields = ('name', 'merchant__user__username', 'category__name')
    list_filter = ('merchant', 'category', 'is_available')

    def get_merchant_name(self, obj):
        return obj.merchant.store_name if obj.merchant else "Merchant not specified"
    get_merchant_name.short_description = "Merchant"

# Order management
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'get_merchant_name', 'total_price', 'status', 'created_at')
    search_fields = ('order_number', 'customer__username')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)

    def get_queryset(self, request):
        """ Optimize query to reduce database queries """
        return super().get_queryset(request).select_related('customer', 'merchant')

    def get_merchant_name(self, obj):
        return obj.merchant.store_name if obj.merchant else "Merchant not specified"
    get_merchant_name.short_description = "Merchant"

# Order item management
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'get_merchant_name')
    search_fields = ('order__order_number', 'item__name', 'item__merchant__store_name')

    def get_merchant_name(self, obj):
        return obj.item.merchant.store_name
    get_merchant_name.short_description = 'Merchant'

# Review management
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'order', 'rating', 'created_at')
    search_fields = ('user__username', 'item__name', 'order__order_number')
    list_filter = ('rating', 'created_at')