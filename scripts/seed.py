import os
import django

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Bubble_Tea_Shop.settings")
django.setup()

from django.contrib.auth.models import User
from shop.models import Merchant, Category, Item, Order, OrderItem, Review


def create_admin_user():
	""" 创建超级用户 """
	if not User.objects.filter(username="admin").exists():
		User.objects.create_superuser("admin", "admin@example.com", "admin123")
		print("创建超级用户: admin / admin123")
	else:
		print("超级用户已存在")


def create_merchants():
	""" 创建商家 """
	user, created = User.objects.get_or_create(username="merchant1", defaults={"email": "merchant1@example.com"})
	merchant, created = Merchant.objects.get_or_create(user=user, store_name="I Feel Bubble Tea")
	print("商家创建成功:", merchant.store_name)


def create_categories():
	""" 创建商品类别 """
	categories = ["奶茶", "果茶", "咖啡", "小吃"]
	for name in categories:
		Category.objects.get_or_create(name=name)
	print("商品类别已添加")


def create_items():
	""" 创建商品 """
	merchant = Merchant.objects.first()
	category = Category.objects.filter(name="奶茶").first()

	items = [
		{"name": "珍珠奶茶", "description": "经典珍珠奶茶", "price": 5.99},
		{"name": "红豆奶茶", "description": "红豆与奶茶的完美结合", "price": 6.50},
		{"name": "抹茶拿铁", "description": "抹茶加牛奶，健康美味", "price": 7.00},
	]

	for item in items:
		Item.objects.get_or_create(merchant=merchant, name=item["name"], defaults={
			"description": item["description"],
			"price": item["price"],
			"category": category
		})
	print("商品已添加")


def create_orders():
	""" 创建测试订单 """
	user = User.objects.filter(username="customer1").first()
	if not user:
		user = User.objects.create_user(username="customer1", email="customer1@example.com", password="customer123")

	item = Item.objects.first()
	order = Order.objects.create(user=user, total_price=item.price, status="Pending")
	OrderItem.objects.create(order=order, item=item, quantity=1)

	print(f"订单创建成功: {order.id}")


def create_reviews():
	""" 添加商品评价 """
	user = User.objects.filter(username="customer1").first()
	item = Item.objects.first()
	Review.objects.get_or_create(user=user, item=item, defaults={
		"rating": 5,
		"comment": "奶茶很好喝！"
	})
	print("评价已添加")


if __name__ == "__main__":
	create_admin_user()
	create_merchants()
	create_categories()
	create_items()
	create_orders()
	create_reviews()
	print("数据库初始化完成！🎉")