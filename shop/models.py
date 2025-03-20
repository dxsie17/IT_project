from django.db import models
from django.contrib.auth.models import User
import uuid
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from django.utils.text import slugify


# User Profile (including both merchants and regular users)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_merchant = models.BooleanField(default=False)  # Whether the user is a merchant
    store_name = models.CharField(max_length=255, blank=True, null=True)  # Only merchants have a store name
    store_slug = models.SlugField(unique=True, blank=True, null=True)  # Slug field for URL
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Store creation time for merchants

    def save(self, *args, **kwargs):
        # **Regular users do not get assigned a store_slug**
        if not self.is_merchant:
            self.store_slug = None  # Ensure store_slug is NULL for regular users
        else:
            # **Ensure merchants have a unique store_slug**
            if not self.store_slug or self.store_slug.strip() == '':
                base_slug = slugify(self.store_name) if self.store_name else f"merchant-{self.id}"
                unique_slug = base_slug
                counter = 1

                while UserProfile.objects.filter(store_slug=unique_slug).exclude(pk=self.pk).exists():
                    unique_slug = f"{base_slug}-{counter}"
                    counter += 1

                self.store_slug = unique_slug

        super().save(*args, **kwargs)

    def __str__(self):
        if self.is_merchant:
            return f"Merchant: {self.store_name}"
        return f"User: {self.user.username}"


# Product Category
class Category(models.Model):
    """ Product categories, each merchant has their own categories """
    merchant = models.ForeignKey(
        UserProfile,  # Link to merchant
        on_delete=models.CASCADE,
        related_name="categories",
        limit_choices_to={'is_merchant': True}  # Only merchants can create categories
    )
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('merchant', 'name')  # Ensure category names are unique within the same merchant

    def __str__(self):
        return f"{self.merchant.store_name} - {self.name}"


# Product Information
class Item(models.Model):
    merchant = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        limit_choices_to={'is_merchant': True},
        related_name="merchant_items"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="items")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


def generate_unique_order_number():
    """ 生成唯一的订单号 """
    while True:
        order_number = uuid.uuid4().hex[:10].upper()  # 生成 10 位随机字符串
        if not Order.objects.filter(order_number=order_number).exists():
            return order_number


# Order Model
class Order(models.Model):
    order_number = models.CharField(
        max_length=20, unique=True, default=uuid.uuid4().hex[:10].upper()
    )  # Order number
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customer_orders")  # User who placed the order
    merchant = models.ForeignKey(UserProfile, on_delete=models.CASCADE, limit_choices_to={'is_merchant': True}, related_name="merchant_orders", null=False, blank=False)
    items = models.ManyToManyField(Item, through='OrderItem')  # Products included in the order
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Total price

    # Order Status Choices
    status_choices = [
        ('Ongoing', 'Ongoing'),
        ('Finished', 'Finished'),
        ('Canceled', 'Canceled'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='Ongoing')  # Order status
    created_at = models.DateTimeField(auto_now_add=True)  # Order creation time
    updated_at = models.DateTimeField(auto_now=True)  # Order update time

    def save(self, *args, **kwargs):
        if not self.order_number:  # 仅在 order_number 为空时生成
            self.order_number = self.generate_unique_order_number()
        super().save(*args, **kwargs)

    def update_total_price(self):
        """ Calculate the total price of the order """
        total = self.order_items.aggregate(
            total=Sum(F('quantity') * F('item__price'), output_field=models.DecimalField())
        )['total'] or 0.00

        self.total_price = total
        self.save(update_fields=['total_price'])

    def __str__(self):
        return f"Order {self.order_number} - {self.status}"


# Order Items (Products within an Order)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="ordered_items")  # Added related_name
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('order', 'item')  # Ensure each order contains a unique product

    def get_total_price(self):
        """Calculate the total price for this item in the order"""
        return float(self.item.price) * self.quantity

    def save(self, *args, **kwargs):
        """After saving OrderItem, update Order total price"""
        super().save(*args, **kwargs)
        self.order.update_total_price()  # Automatically update order total price

    def delete(self, *args, **kwargs):
        """After deleting OrderItem, update Order total price"""
        super().delete(*args, **kwargs)
        self.order.update_total_price()  # Automatically update order total price

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"


# Ratings and Reviews
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True, related_name="reviews")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True, related_name="order_reviews")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Ratings from 1 to 5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """ Ensure that either `item` or `order` exists, but not both """
        if self.item and self.order:
            raise ValidationError("A review cannot be for both an item and an order at the same time. Please choose one.")
        if not self.item and not self.order:
            raise ValidationError("A review must be associated with either an item or an order.")

    def __str__(self):
        if self.item:
            return f"User {self.user.username} reviewed {self.item.name}"
        return f"User {self.user.username} reviewed Order {self.order.order_number}"