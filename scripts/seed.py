import os
import django
from django.utils.timezone import now

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop.settings")
django.setup()

from django.contrib.auth.models import User
from shop.models import Merchant, Category, Item, Order, OrderItem, Review


def create_admin_user():
    """ 创建超级用户 """
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@example.com", "admin123")
        print("✅ 创建超级用户: admin / admin123")
    else:
        print("✅ 超级用户已存在")


def create_merchants():
    """ 创建商家 """
    user, _ = User.objects.get_or_create(username="merchant1", defaults={"email": "merchant1@example.com"})
    merchant, _ = Merchant.objects.get_or_create(user=user, store_name="I Feel")
    print(f"✅ 商家创建成功: {merchant.store_name}")


def create_categories():
    """ 创建商品类别 """
    categories = ["奶茶", "果茶", "咖啡", "小吃"]
    for name in categories:
        Category.objects.get_or_create(name=name)
    print("✅ 商品类别已添加")


def create_items():
    """ 创建商品 """
    merchant = Merchant.objects.first()
    if not merchant:
        print("❌ 错误: 没有找到商家，请先创建商家！")
        return

    category = Category.objects.filter(name="奶茶").first()
    if not category:
        print("❌ 错误: 没有找到类别，请先创建类别！")
        return

    items = [
        {"name": "珍珠奶茶", "description": "经典珍珠奶茶", "price": 5.99},
        {"name": "红豆奶茶", "description": "红豆与奶茶的完美结合", "price": 6.50},
        {"name": "抹茶拿铁", "description": "抹茶加牛奶，健康美味", "price": 7.00},
    ]

    for item in items:
        Item.objects.get_or_create(
            merchant=merchant,
            name=item["name"],
            defaults={"description": item["description"], "price": item["price"], "category": category},
        )
    print("✅ 商品已添加")


def create_orders():
    """ 创建测试订单 """
    user, _ = User.objects.get_or_create(username="customer1", defaults={"email": "customer1@example.com", "password": "customer123"})

    items = list(Item.objects.all())  # 获取所有商品
    if not items:
        print("❌ 错误: 订单创建失败，未找到商品！")
        return

    # 确保 order_number 唯一
    order_number_1 = "0001"
    order_number_2 = "0002"

    order1, created1 = Order.objects.get_or_create(
        order_number=order_number_1,
        defaults={"customer": user, "total_price": items[0].price * 2, "status": "Ongoing", "created_at": now()}
    )

    order2, created2 = Order.objects.get_or_create(
        order_number=order_number_2,
        defaults={"customer": user, "total_price": items[1].price * 1, "status": "Finished", "created_at": now()}
    )

    if created1:
        OrderItem.objects.create(order=order1, item=items[0], quantity=2)
        print(f"✅ 订单创建成功: {order1.order_number}")
    else:
        print(f"✅ 订单已存在: {order1.order_number}")

    if created2:
        OrderItem.objects.create(order=order2, item=items[1], quantity=1)
        print(f"✅ 订单创建成功: {order2.order_number}")
    else:
        print(f"✅ 订单已存在: {order2.order_number}")


def create_reviews():
    """ 添加商品评价 """
    user = User.objects.filter(username="customer1").first()
    if not user:
        print("❌ 错误: 没有找到用户，请先创建用户！")
        return

    items = list(Item.objects.all())
    if not items:
        print("❌ 错误: 没有找到商品，请先创建商品！")
        return

    reviews = [
        {"item": items[0], "rating": 5, "comment": "这款珍珠奶茶太棒了，珍珠Q弹，奶茶很香！"},
        {"item": items[1], "rating": 4, "comment": "红豆奶茶很好喝，就是有点甜了"},
        {"item": items[2], "rating": 5, "comment": "抹茶拿铁味道刚刚好，喜欢"},
    ]

    for review in reviews:
        Review.objects.get_or_create(
            user=user,
            item=review["item"],
            defaults={
                "rating": review["rating"],
                "comment": review["comment"],
            },
        )
    print("✅ 评论数据已添加")


if __name__ == "__main__":
    create_admin_user()
    create_merchants()
    create_categories()
    create_items()
    create_orders()
    create_reviews()
    print("🎉 数据库初始化完成！")