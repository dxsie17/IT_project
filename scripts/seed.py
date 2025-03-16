import os
import django

# **1️⃣ 确保 Django 设置正确**
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "it_project.settings")  # 替换 "it_project" 为你的项目名
django.setup()  # **必须在 models 导入前执行**

from django.utils.timezone import now
from django.contrib.auth.models import User
from shop.models import Merchant, UserProfile, Category, Item, Order, OrderItem, Review

def create_users():
    """ 创建超级管理员、商家和用户 """
    admin_user, created = User.objects.get_or_create(username="admin", defaults={
        "email": "admin@example.com", "is_staff": True, "is_superuser": True
    })
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
        print("✅ 超级管理员创建成功: admin / admin123")

    merchant_user, created = User.objects.get_or_create(username="merchant1", defaults={
        "email": "merchant1@example.com", "is_staff": True
    })
    if created:
        merchant_user.set_password("merchant_password123")
        merchant_user.save()
        print("✅ 商家账号创建成功: merchant1 / merchant_password123")

    customer_user, created = User.objects.get_or_create(username="customer1", defaults={
        "email": "customer1@example.com"
    })
    if created:
        customer_user.set_password("customer_password123")
        customer_user.save()
        print("✅ 用户账号创建成功: customer1 / customer_password123")


def create_profiles():
    """ 为商家和用户创建 UserProfile """
    merchant_user = User.objects.get(username="merchant1")
    customer_user = User.objects.get(username="customer1")

    merchant_profile, created = UserProfile.objects.get_or_create(user=merchant_user, defaults={"is_merchant": True})
    if created:
        print("✅ 商家 Profile 创建成功")

    customer_profile, created = UserProfile.objects.get_or_create(user=customer_user, defaults={"is_merchant": False})
    if created:
        print("✅ 用户 Profile 创建成功")


def create_merchant():
    """ 创建商家信息 """
    merchant_user = User.objects.get(username="merchant1")
    merchant, created = Merchant.objects.get_or_create(user=merchant_user, store_name="I Feel Tea Shop")
    if created:
        print("✅ 商家信息创建成功: I Feel Tea Shop")


def create_categories():
    """ 创建商品类别 """
    categories = ["奶茶", "果茶", "咖啡", "小吃"]
    for name in categories:
        Category.objects.get_or_create(name=name)
    print("✅ 商品类别已添加")


def create_items():
    """ 创建商品 """
    merchant = Merchant.objects.first()
    category = Category.objects.filter(name="奶茶").first()

    if not merchant or not category:
        print("❌ 商家或类别未找到，无法创建商品")
        return

    items = [
        {"name": "珍珠奶茶", "description": "经典珍珠奶茶", "price": 5.99},
        {"name": "红豆奶茶", "description": "红豆与奶茶的完美结合", "price": 6.50},
        {"name": "抹茶拿铁", "description": "抹茶加牛奶，健康美味", "price": 7.00},
    ]

    for item in items:
        Item.objects.get_or_create(
            merchant=merchant, name=item["name"],
            defaults={"description": item["description"], "price": item["price"], "category": category}
        )
    print("✅ 商品数据已添加")


def create_orders():
    """ 创建测试订单 """
    customer = User.objects.get(username="customer1")
    items = list(Item.objects.all())

    if not items:
        print("❌ 无商品，无法创建订单")
        return

    order1, created1 = Order.objects.get_or_create(
        order_number="0001",
        defaults={"customer": customer, "total_price": items[0].price * 2, "status": "Ongoing", "created_at": now()}
    )

    order2, created2 = Order.objects.get_or_create(
        order_number="0002",
        defaults={"customer": customer, "total_price": items[1].price, "status": "Finished", "created_at": now()}
    )

    if created1:
        OrderItem.objects.create(order=order1, item=items[0], quantity=2)
        print(f"✅ 订单创建成功: {order1.order_number}")

    if created2:
        OrderItem.objects.create(order=order2, item=items[1], quantity=1)
        print(f"✅ 订单创建成功: {order2.order_number}")


def create_reviews():
    """ 添加商品评价 """
    customer = User.objects.get(username="customer1")
    items = list(Item.objects.all())

    if not items:
        print("❌ 无商品，无法创建评论")
        return

    reviews = [
        {"item": items[0], "rating": 5, "comment": "珍珠奶茶太棒了！"},
        {"item": items[1], "rating": 4, "comment": "红豆奶茶很好喝，但有点甜"},
        {"item": items[2], "rating": 5, "comment": "抹茶拿铁味道很好"},
    ]

    for review in reviews:
        Review.objects.get_or_create(
            user=customer,
            item=review["item"],
            defaults={"rating": review["rating"], "comment": review["comment"]}
        )
    print("✅ 评论数据已添加")


if __name__ == "__main__":
    create_users()
    create_profiles()
    create_merchant()
    create_categories()
    create_items()
    create_orders()
    create_reviews()
    print("🎉 数据填充完成！")