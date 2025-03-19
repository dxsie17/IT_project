import json
from decimal import Decimal

from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Item, Order, OrderItem, Review, UserProfile, Category
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
"""
用户端
"""


# 商品列表
def product_list(request):
	return render(request, "home.html")

from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from shop.models import UserProfile
from django.contrib.auth.models import User

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # 检查用户名是否存在
        user = User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({"success": False, "error": "用户不存在，请检查用户名或注册"}, status=400)

        # 认证用户
        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse({"success": False, "error": "密码错误，请重新输入"}, status=400)

        auth_login(request, user)

        # 判断是否是商家
        if hasattr(user, "userprofile") and user.userprofile.is_merchant:
            return JsonResponse({"success": True, "redirect_url": "/merchant/"})
        else:
            return JsonResponse({"success": True, "redirect_url": "/users/"})

    return render(request, "login.html")


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        tel = request.POST.get("tel")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        is_merchant = request.POST.get("is_merchant") == "on"  # 获取复选框状态

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect("register")

        # 创建 User
        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()

        # 关联 UserProfile
        user_profile = UserProfile.objects.create(user=user, phone_number=tel, is_merchant=is_merchant)
        user_profile.save()

        login(request, user)  # 直接登录用户
        return redirect("dashboard")  # 注册成功后重定向

    return render(request, "register.html")


def custom_logout(request):
	logout(request)
	return redirect('product_list')


### 用户端
@login_required
def users_takeorder(request):
	categories = Category.objects.all()
	default_category = categories.first()
	items = Item.objects.filter(category=default_category, is_available=True)

	selected_category = request.GET.get('category')
	if selected_category:
		items = Item.objects.filter(category__name=selected_category, is_available=True)

	return render(request, "user/takeorder.html", {
		'categories': categories,
		'items': items,
		'selected_category': selected_category
	})


@login_required
def item_details(request, item_id):
    """获取商品详细信息"""
    try:
        item = Item.objects.get(id=item_id, merchant=request.user.userprofile)
        categories = Category.objects.all().values("id", "name")

        return JsonResponse({
            "id": item.id,
            "name": item.name,
            "price": str(item.price),
            "description": item.description,
            "image": item.image.url if item.image else None,
            "category": item.category.id if item.category else None,
            "categories": list(categories)
        })
    except Item.DoesNotExist:
        return JsonResponse({"error": "商品不存在"}, status=404)


@login_required
def add_to_basket(request, item_id):
	item = get_object_or_404(Item, id=item_id)

	order, created = Order.objects.get_or_create(
		customer=request.user,
		status='Ongoing',
		defaults={'total_price': 0}
	)

	order_item, created = OrderItem.objects.get_or_create(
		order=order,
		item=item,
		defaults={'quantity': 1}
	)

	if not created:
		order_item.quantity += 1
		order_item.save()

	return JsonResponse({'success': True})

@login_required
def decrease_from_basket(request, item_id):
    """减少购物车中某个商品的数量"""
    item = get_object_or_404(Item, id=item_id)
    order = Order.objects.filter(customer=request.user, status='Ongoing').first()

    if not order:
        return JsonResponse({'success': False, 'error': '购物车为空'}, status=400)

    try:
        order_item = OrderItem.objects.get(order=order, item=item)
        if order_item.quantity > 1:
            order_item.quantity -= 1
            order_item.save()
        else:
            order_item.delete()

        # 检查订单是否已清空，如果是，则删除订单
        if not order.order_items.exists():
            order.delete()

        return JsonResponse({'success': True})
    except OrderItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': '商品不在购物车中'}, status=400)


@login_required
def remove_from_basket(request, item_id):
    """从购物车中移除某个商品"""
    item = get_object_or_404(Item, id=item_id)
    order = Order.objects.filter(customer=request.user, status='Ongoing').first()

    if not order:
        return JsonResponse({'success': False, 'error': '订单不存在'}, status=400)

    try:
        order_item = OrderItem.objects.get(order=order, item=item)
        order_item.delete()

        # 如果购物车为空，则删除订单
        if not OrderItem.objects.filter(order=order).exists():
            order.delete()

        return JsonResponse({'success': True, 'message': '商品已移除'})
    except OrderItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': '商品不在购物车中'}, status=400)


@login_required
def get_cart(request):
    """获取购物车"""
    order = Order.objects.filter(customer=request.user, status='Ongoing').first()
    cart_items = []

    if order:
        cart_items = [{
            'id': oi.item.id,
            'name': oi.item.name,
            'quantity': oi.quantity,
            'unit_price': float(oi.item.price),  # 改为 float 类型
            'total_price': float(oi.item.price * oi.quantity)
        } for oi in order.orderitem_set.all()]

    return JsonResponse({'items': cart_items})


"""
商家端
"""


@login_required
def merchant_dashboard(request):
    try:
        user_profile = request.user.userprofile
        if not user_profile.is_merchant:
            return redirect("product_list")

        # 读取查询参数，默认显示进行中的订单
        status_filter = request.GET.get("status", "Ongoing")

        # 只获取该商家的订单
        orders = Order.objects.filter(merchant=user_profile, status=status_filter).prefetch_related("order_items__item")

        # 该商家所有商品
        items = Item.objects.filter(merchant=user_profile)

        # 获取商家名称
        store_name = user_profile.store_name  # 确保 UserProfile 或 Merchant 模型中有 `store_name` 字段

    except UserProfile.DoesNotExist:
        return redirect("product_list")

    return render(request, "merchant/dashboard.html", {
        "orders": orders,
        "items": items,
        "status_filter": status_filter,
        "store_name": store_name  # 传递 store_name
    })


"""商品管理"""


@login_required
def manage_items(request):
    """商家管理商品（返回 JSON 数据）"""
    merchant_profile = request.user.userprofile
    category_id = request.GET.get("category_id")

    if category_id:
        items = Item.objects.filter(merchant=merchant_profile, category_id=category_id)
    else:
        items = Item.objects.filter(merchant=merchant_profile)

    items_data = [
        {
            "id": item.id,
            "name": item.name,
            "price": str(item.price),
            "image": item.image.url if item.image else None,
            "is_available": item.is_available,
            "category": item.category.name if item.category else "未分类",
        }
        for item in items
    ]

    return JsonResponse({"items": items_data})

@login_required
def get_categories(request):
    """返回当前商家有商品的类别"""
    if not request.user.userprofile.is_merchant:
        return JsonResponse({'error': '无权限访问'}, status=403)

    merchant_profile = request.user.userprofile
    # 仅返回当前商家有商品的类别
    categories = Category.objects.all().values("id", "name").distinct()
    # 检查是否返回正确的类别
    print(f"商家 {merchant_profile.store_name} 的类别: {list(categories)}")

    return JsonResponse({'categories': list(categories)})

"""添加商品类别"""

@login_required
def add_category(request):
    """商家添加新类别"""
    if request.method == "POST":
        category_name = request.POST.get("category_name", "").strip()

        if not category_name:
            return JsonResponse({'success': False, 'error': '类别名称不能为空'}, status=400)

        # 避免重复类别
        if Category.objects.filter(name=category_name).exists():
            return JsonResponse({'success': False, 'error': '该类别已存在'}, status=400)

        try:
            new_category = Category.objects.create(name=category_name)
            return JsonResponse({'success': True, 'message': '类别添加成功', 'category': {'id': new_category.id, 'name': new_category.name}})
        except IntegrityError:
            return JsonResponse({'success': False, 'error': '数据库错误，请重试'}, status=500)

    return JsonResponse({'error': '仅支持 POST 请求'}, status=405)


"""商家添加、编辑商品"""
@login_required
def add_item(request):
    """商家添加新商品"""
    if not request.user.userprofile.is_merchant:
        return redirect("product_list")

    categories = Category.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category_id")
        price = request.POST.get("price")
        image = request.FILES.get("image")

        category = get_object_or_404(Category, id=category_id)

        # 创建商品
        Item.objects.create(
            name=name,
            category=category,
            price=price,
            image=image,
            merchant=request.user.userprofile,
            is_available=True,  # 默认上架
        )
        return redirect("manage_items")

    return render(request, "merchant/add_item.html", {"categories": categories})

@login_required
def toggle_item_availability(request, item_id):
    """上架/下架商品"""
    item = get_object_or_404(Item, id=item_id, merchant=request.user.userprofile)

    # 取反商品状态
    item.is_available = not item.is_available
    item.save()

    return JsonResponse({"success": True, "new_status": item.is_available})

@login_required
def edit_item(request, item_id):
    """商家编辑已有商品"""
    item = get_object_or_404(Item, id=item_id, merchant=request.user.userprofile)
    categories = Category.objects.all()

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category_id")
        price = request.POST.get("price")
        image = request.FILES.get("image")

        category = get_object_or_404(Category, id=category_id)

        item.name = name
        item.category = category
        item.price = price
        if image:
            item.image = image
        item.save()

        return redirect("manage_items")

    return render(request, "merchant/edit_item.html", {"item": item, "categories": categories})

@login_required
def delete_item(request, item_id):
    """删除商品（仅商家可操作）"""
    item = get_object_or_404(Item, id=item_id)

    if item.merchant != request.user.userprofile:
        return JsonResponse({'success': False, 'error': '你无权删除此商品'}, status=403)

    # 检查商品是否仍在订单中
    if OrderItem.objects.filter(item=item).exists():
        return JsonResponse({'success': False, 'error': '无法删除，该商品仍然存在于订单中'}, status=400)

    item.delete()
    return JsonResponse({'success': True, 'message': '商品已成功删除'})


@login_required
def update_item(request, item_id):
    """更新商品信息，包括上传图片"""
    if request.method == "POST":
        try:
            name = request.POST.get("name")
            price = request.POST.get("price")
            description = request.POST.get("description", "")
            category_id = request.POST.get("category")
            image = request.FILES.get("image")  # 获取上传的图片

            if not name or not price:
                return JsonResponse({"success": False, "error": "商品名称和价格不能为空！"}, status=400)

            # **判断是更新还是创建**
            if item_id == "new":
                item = Item(
                    name=name,
                    price=Decimal(price),
                    description=description,
                    merchant=request.user.userprofile,  # **确保商品属于当前商家**
                )
                message = "商品已创建！"
            else:
                item = get_object_or_404(Item, id=item_id, merchant=request.user.userprofile)
                item.name = name
                item.price = Decimal(price)
                item.description = description
                message = "商品信息已更新！"

            # **更新分类**
            if category_id:
                item.category = get_object_or_404(Category, id=category_id)

            # **更新图片（如果用户上传了新图片）**
            if image:
                item.image = image

            item.save()

            return JsonResponse({"success": True, "message": message, "item_id": item.id})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "无效请求"}, status=400)

"""商家管理订单"""


@login_required
def merchant_orders(request):
    """商家管理订单"""
    if not request.user.userprofile.is_merchant:
        return redirect("/")

    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "Ongoing")

    # 直接获取商家相关的订单
    orders = Order.objects.filter(merchant=request.user.userprofile, status=status_filter).distinct()

    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(order_items__item__name__icontains=search_query)
        ).distinct()

    return render(request, "merchant/orders.html", {"orders": orders, "status_filter": status_filter})


@login_required
def update_order_status(request, order_id):
    """商家更新订单状态"""
    if not request.user.userprofile.is_merchant:
        return JsonResponse({'error': '无权限访问'}, status=403)

    order = get_object_or_404(Order, id=order_id)

    # 仅允许修改包含自己商品的订单
    merchant_items_in_order = OrderItem.objects.filter(
        order=order, item__merchant=request.user.userprofile
    ).exists()

    if not merchant_items_in_order:
        return JsonResponse({'error': '你无权修改此订单'}, status=403)

    if request.method == "POST":
        new_status = request.POST.get("status", "")
        valid_statuses = [s[0] for s in Order.status_choices]

        if new_status in valid_statuses:
            order.status = new_status
            order.save()
            return JsonResponse({'success': True, 'message': '订单状态已更新'})

        return JsonResponse({'error': '无效的订单状态'}, status=400)

    return JsonResponse({'error': '请求错误'}, status=400)

def get_reviews(request):
    reviews = Review.objects.all().order_by('-created_at')  # 按创建时间倒序排序
    review_list = [
        {
            "username": review.user.username if review.user else "匿名用户",
            "item": review.item.name if review.item else None,
            "order": review.order.order_number if review.order else None,
            "rating": review.rating,
            "comment": review.comment,
            "timestamp": review.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for review in reviews
    ]
    return JsonResponse({"reviews": review_list})