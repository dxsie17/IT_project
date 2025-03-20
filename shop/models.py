from django.db import models
from django.contrib.auth.models import User
import uuid
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from django.utils.text import slugify


# 用户扩展（包括商家和普通用户）
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_merchant = models.BooleanField(default=False)  # 是否是商家
    store_name = models.CharField(max_length=255, blank=True, null=True)  # 商家才有店铺名
    store_slug = models.SlugField(unique=True, blank=True, null=True)  # 用于 URL 的 slug 字段
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # 商家创建时间

    def save(self, *args, **kwargs):
        # **普通用户不分配 store_slug**
        if not self.is_merchant:
            self.store_slug = None  # 确保普通用户的 store_slug 为 NULL
        else:
            # **确保商家有唯一的 store_slug**
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
            return f"商家: {self.store_name}"
        return f"用户: {self.user.username}"


# 商品类别
class Category(models.Model):
    """ 商品类别，每个商家有自己的类别 """
    merchant = models.ForeignKey(
        UserProfile,  # 关联商家
        on_delete=models.CASCADE,
        related_name="categories",
        limit_choices_to={'is_merchant': True}  # 只能是商家
    )
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('merchant', 'name')  # 确保同一商家下类别唯一

    def __str__(self):
        return f"{self.merchant.store_name} - {self.name}"

# 商品信息
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

def generate_order_number():
    return uuid.uuid4().hex[:10].upper()

# 订单
class Order(models.Model):
    order_number = models.CharField(
        max_length=20, unique=True, default=uuid.uuid4().hex[:10].upper()
    )  # 订单编号
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customer_orders")  # 下单用户
    merchant = models.ForeignKey(UserProfile, on_delete=models.CASCADE, limit_choices_to={'is_merchant': True}, related_name="merchant_orders", null=False, blank=False)
    items = models.ManyToManyField(Item, through='OrderItem')  # 订单包含的商品
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # 总价
    # 订单状态
    status_choices = [
        ('Ongoing', '进行中'),
        ('Finished', '已完成'),
        ('Canceled', '已取消'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='Ongoing')  # 订单状态
    created_at = models.DateTimeField(auto_now_add=True)  # 订单建立时间
    updated_at = models.DateTimeField(auto_now=True)  # 订单更新时间

    def update_total_price(self):
        """ 计算订单总价 """
        total = self.order_items.aggregate(
            total=Sum(F('quantity') * F('item__price'), output_field=models.DecimalField())
        )['total'] or 0.00

        self.total_price = total
        self.save(update_fields=['total_price'])

    def __str__(self):
        return f"Order {self.order_number} - {self.status}"

# 订单中的商品详情
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="ordered_items")  # 增加 related_name
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('order', 'item')  # 添加唯一性约束


    def get_total_price(self):
        """计算当前商品在订单中的总价"""
        return float(self.item.price) * self.quantity

    def save(self, *args, **kwargs):
        """保存 OrderItem 后更新 Order 总价"""
        super().save(*args, **kwargs)
        self.order.update_total_price()  # 订单自动更新总价

    def delete(self, *args, **kwargs):
        """删除 OrderItem 后更新 Order 总价"""
        super().delete(*args, **kwargs)
        self.order.update_total_price()  # 订单自动更新总价

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"

# 评分与评论
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True, related_name="reviews")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True, related_name="order_reviews")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 评分
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """ 确保 `item` 和 `order` 只能存在一个 """
        if self.item and self.order:
            raise ValidationError("评论不能同时针对商品和订单，请选择一个")
        if not self.item and not self.order:
            raise ValidationError("评论必须针对一个商品或订单")

    def __str__(self):
        if self.item:
            return f"用户 {self.user.username} 对 {self.item.name} 的评价"
        return f"用户 {self.user.username} 对订单 {self.order.order_number} 的评价"