from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return self.name

# 商品信息
class Item(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)  # 关联商家
    name = models.CharField(max_length=255)  # 商品名称
    description = models.TextField(blank=True)  # 商品描述
    price = models.DecimalField(max_digits=10, decimal_places=2)  # 商品价格
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)  # 关联类别
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # 商品图片

    def __str__(self):
        return self.name

# 订单
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 下单用户
    items = models.ManyToManyField(Item, through='OrderItem')  # 订单包含的商品
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # 总价
    status_choices = [
        ('Pending', '待支付'),
        ('Paid', '已支付'),
        ('Shipped', '已发货'),
        ('Completed', '已完成'),
        ('Cancelled', '已取消'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"订单 {self.id} - {self.status}"

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