from django.db import models
from django.contrib.auth.models import User
import uuid

# 用户扩展：区分商家和普通用户
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_merchant = models.BooleanField(default=False)  # 是否是商家

    def __str__(self):
        return f"{self.user.username} - {'商家' if self.is_merchant else '普通用户'}"

# 商家信息
class Merchant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # 绑定 Django 自带的 User
    store_name = models.CharField(max_length=255)  # 店铺名称
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_name

# 商品类别
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_addon = models.BooleanField(default=False)  # 是否是小料类别

    def __str__(self):
        return self.name

# 商品信息
class Item(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)  # 关联商家
    name = models.CharField(max_length=255)  # 商品名称
    description = models.TextField(blank=True)  # 商品描述
    price = models.DecimalField(max_digits=10, decimal_places=2)  # 商品价格
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)  # 关联类别
    image = models.ImageField(upload_to='Items/', blank=True, null=True)  # 商品图片
    is_available = models.BooleanField(default=True)  # 是否在售

    def __str__(self):
        return self.name

# 订单
class Order(models.Model):
    order_number = models.CharField(
        max_length=20, unique=True, default=uuid.uuid4().hex[:10].upper()
    )  # 订单编号
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="customer_orders"
    )  # 下单用户
    items = models.ManyToManyField(Item, through='OrderItem')  # 订单包含的商品
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # 总价
    payment_time = models.DateTimeField(blank=True, null=True) # 支付时间
    remark = models.TextField(blank=True, null=True) # 订单评论
    # 订单状态
    status_choices = [
        ('Ongoing', '进行中'),
        ('Finished', '已完成'),
        ('Canceled', '已取消'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='Ongoing') # 订单状态
    created_at = models.DateTimeField(auto_now_add=True) #订单建立时间
    updated_at = models.DateTimeField(auto_now=True) # 订单更新时间


    def __str__(self):
        return f"Order {self.order_number} - {self.status}"

# 订单中的商品详情
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"

# 评分与评论
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 评分
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"用户 {self.user.username} 对 {self.item.name} 的评价"