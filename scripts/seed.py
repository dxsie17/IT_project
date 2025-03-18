import os
import django
from django.utils.timezone import now

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "it_project.settings")
django.setup()

from django.contrib.auth.models import User
from shop.models import UserProfile, Category, Item, Order, OrderItem, Review

def reset_database():
    """ 删除所有测试数据（订单、订单项、评论、商品），但保留用户和商家信息 """
    print("🧹 正在清除旧数据...")

    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    Review.objects.all().delete()
    Item.objects.all().delete()
    Category.objects.all().delete()

    print("✅ 旧数据已清除")

def create_merchants():
    """ 确保商家账户存在（不会重复创建） """
    user1, _ = User.objects.get_or_create(username="merchant1", defaults={"email": "merchant1@example.com"})
    user2, _ = User.objects.get_or_create(username="merchant2", defaults={"email": "merchant2@example.com"})

    merchant1, _ = UserProfile.objects.get_or_create(user=user1, defaults={"is_merchant": True, "store_name": "I Feel 奶茶"})
    merchant2, _ = UserProfile.objects.get_or_create(user=user2, defaults={"is_merchant": True, "store_name": "Tea Queen"})

    print(f"✅ 商家账户检查完成: {merchant1.store_name}, {merchant2.store_name}")

def create_categories():
    """ 确保类别不会重复创建 """
    categories = ["奶茶", "果茶", "咖啡", "小吃"]
    for name in categories:
        Category.objects.get_or_create(name=name)
    print("✅ 商品类别已添加")

def create_items():
    """ 重新填充商品（不会重复创建） """
    merchants = UserProfile.objects.filter(is_merchant=True)
    if not merchants:
        print("❌ 没有找到商家，请先创建商家！")
        return

    categories = {c.name: c for c in Category.objects.all()}
    if not categories:
        print("❌ 没有找到类别，请先创建类别！")
        return

    items_data = [
        {"name": "珍珠奶茶", "desc": "经典珍珠奶茶", "price": 5.99, "category": "奶茶", "merchant": merchants[0]},
        {"name": "红豆奶茶", "desc": "红豆与奶茶的完美结合", "price": 6.50, "category": "奶茶", "merchant": merchants[0]},
        {"name": "抹茶拿铁", "desc": "抹茶加牛奶，健康美味", "price": 7.00, "category": "咖啡", "merchant": merchants[1]},
    ]

    for item in items_data:
        Item.objects.get_or_create(
            merchant=item["merchant"],
            name=item["name"],
            defaults={"description": item["desc"], "price": item["price"], "category": categories[item["category"]]},
        )
    print("✅ 商品已重新填充")

def create_orders():
    """ 创建多个 Ongoing 订单（不会重复创建用户） """
    customer, _ = User.objects.get_or_create(username="customer1", defaults={"email": "customer1@example.com"})
    customer_profile, _ = UserProfile.objects.get_or_create(user=customer, defaults={"is_merchant": False})

    items = list(Item.objects.all())
    if not items:
        print("❌ 订单创建失败，未找到商品！")
        return

    # 创建 5 个 Ongoing 订单，每个订单包含多个商品
    for order_num in range(2001, 2006):
        order = Order.objects.create(
            merchant=items[0].merchant,  # 分配给第一个商家
            customer=customer,
            status="Ongoing",
            order_number=str(order_num),
            created_at=now(),
            total_price=0
        )

        # 订单包含 2-3 个不同的商品
        total_price = 0
        for i, item in enumerate(items[:3]):  # 选取前 3 个商品
            quantity = (i + 1)  # 数量依次递增
            OrderItem.objects.create(order=order, item=item, quantity=quantity)
            total_price += item.price * quantity

        # 更新订单总价
        order.total_price = total_price
        order.save()
        print(f"✅ 创建 Ongoing 订单: {order.order_number}，包含 {order.order_items.count()} 件商品，总价：£{order.total_price}")

def create_reviews():
    """ 添加商品评价 """
    user = User.objects.filter(username="customer1").first()
    if not user:
        print("❌ 没有找到用户，请先创建用户！")
        return

    items = list(Item.objects.all())
    if not items:
        print("❌ 没有找到商品，请先创建商品！")
        return

    reviews = [
        {"item": items[0], "rating": 5, "comment": "珍珠Q弹，奶茶很香！"},
        {"item": items[1], "rating": 4, "comment": "红豆奶茶很好喝，就是有点甜了"},
        {"item": items[2], "rating": 5, "comment": "抹茶拿铁味道刚刚好，喜欢"},
    ]

    for review in reviews:
        Review.objects.get_or_create(
            user=user,
            item=review["item"],
            defaults={"rating": review["rating"], "comment": review["comment"]},
        )
    print("✅ 评论数据已添加")

if __name__ == "__main__":
    reset_database()  # 先清空数据
    create_merchants()  # 确保商家存在
    create_categories()  # 确保类别存在
    create_items()  # 重新填充商品
    create_orders()  # 添加新订单
    create_reviews()  # 添加评论
    print("🎉 数据库初始化完成！")