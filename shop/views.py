import json
import traceback
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


"""用户端"""
# 商品列表
def product_list(request):
	return render(request, "home.html")

# 商家/用户登录
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
        user_profile = getattr(user, "userprofile", None)

        # ✅ **商家直接进入自己的店铺**
        if user_profile and user_profile.is_merchant:
            return JsonResponse({"success": True, "redirect_url": "/merchant/"})

        # ✅ **普通用户进入选择商家页面**
        return JsonResponse({"success": True, "redirect_url": "/select-store/"})

    return render(request, "login.html")


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        phone = request.POST.get("phone")  # 修正字段名
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        is_merchant = request.POST.get("is_merchant") == "on"  # 获取复选框状态
        store_name = request.POST.get("store_name") if is_merchant else None

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect("register")

        # 商家必须填写店铺名
        if is_merchant:
            if not store_name or len(store_name.strip()) < 2:
                messages.error(request, "Merchants must fill in a valid store name (at least 2 characters).")
                return redirect("register")
            if UserProfile.objects.filter(store_name=store_name).exists():
                messages.error(request, "Store name already exists.")
                return redirect("register")
        try:
            # 创建 User
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password1
            )
            user.save()

            # 关联 UserProfile
            user_profile = UserProfile.objects.create(
                user=user,
                phone_number=phone,
                is_merchant=is_merchant,
                store_name=store_name
            )
            user_profile.save()

            auth_login(request, user)  # 直接登录用户
            if user_profile.is_merchant:
                messages.success(request, "商家注册成功！")
                return redirect("login")
            else:
                messages.success(request, "注册成功！")
                return redirect("login")

        except Exception as e:
            messages.error(request, f"注册失败: {str(e)}")
            return redirect("register")

    return render(request, "register.html")


def user_logout(request):
	logout(request)
	return redirect('user_login')

@login_required
def select_store(request):
    """ 显示所有商家店铺，供用户选择 """
    merchants = UserProfile.objects.filter(is_merchant=True).values("store_name", "store_slug")
    print("🔍 商家数据:", list(merchants))
    return render(request, "user/select_store.html", {"merchants": merchants})

### 用户端
@login_required
def users_takeorder(request, store_slug):
    # 获取该商家
    merchant = get_object_or_404(UserProfile, store_slug=store_slug, is_merchant=True)
    # 只获取该商家的商品类别
    categories = Category.objects.filter(merchant=merchant)
    default_category = categories.first()
    # 只获取该商家的商品
    items = Item.objects.filter(merchant=merchant, category=default_category, is_available=True)

    selected_category = request.GET.get('category')
    if selected_category:
        items = Item.objects.filter(merchant=merchant, category__name=selected_category, is_available=True)

    return render(request, "user/takeorder.html", {
        'categories': categories,
        'items': items,
        'selected_category': selected_category,
        'merchant': merchant,  # 传递商家信息
    })

### 获取商品
@login_required
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return JsonResponse({
        "id": item.id,
        "name": item.name,
        "price": float(item.price),  # 避免 Decimal 类型
        "description": item.description,
        "image": item.image.url if item.image else None
    })

### 加购物车
@login_required
def add_to_basket(request, item_id):
    """ 添加商品到购物车 """
    try:
        item = get_object_or_404(Item, id=item_id)

        # ✅ 获取商家 ID
        merchant_id = item.merchant.id if item.merchant else None
        if not merchant_id:
            return JsonResponse({"success": False, "error": "商品未绑定商家"}, status=400)

        basket = request.session.get("basket", {})

        if str(item_id) in basket:
            basket[str(item_id)]["quantity"] += 1
        else:
            basket[str(item_id)] = {
                "name": item.name,
                "price": float(item.price),
                "quantity": 1,
                "merchant_id": merchant_id  # ✅ 确保存入商家 ID
            }

        request.session["basket"] = basket
        request.session.modified = True  # ✅ 强制保存 session
        return JsonResponse({"success": True, "message": "商品已加入购物车"})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def decrease_from_basket(request, item_id):
    """ 减少购物车中某个商品的数量 """
    basket = request.session.get("basket", {})

    if str(item_id) in basket:
        if basket[str(item_id)]["quantity"] > 1:
            basket[str(item_id)]["quantity"] -= 1
        else:
            del basket[str(item_id)]  # 数量为 0 时移除商品

    request.session["basket"] = basket
    return JsonResponse({"success": True, "message": "商品数量已更新"})


@login_required
def remove_from_basket(request, item_id):
    """ 从购物车中移除商品 """
    basket = request.session.get("basket", {})

    if str(item_id) in basket:
        del basket[str(item_id)]

    request.session["basket"] = basket
    return JsonResponse({"success": True, "message": "商品已移除"})


@login_required
def get_cart(request):
    """ 获取购物车商品列表及总价 """
    basket = request.session.get("basket", {})

    cart_items = []
    total_price = 0.00

    for item_id, item in basket.items():
        total_price += item["price"] * item["quantity"]
        cart_items.append({
            "id": item_id,
            "name": item["name"],
            "quantity": item["quantity"],
            "unit_price": item["price"],
            "total_price": item["price"] * item["quantity"]
        })

    return JsonResponse({"items": cart_items, "total_price": round(total_price, 2)})


@login_required
def checkout(request):
    """ 用户支付后生成订单 """
    try:
        basket = request.session.get("basket", {})

        if not basket:
            return JsonResponse({"success": False, "error": "购物车为空"}, status=400)

        user = request.user
        orders = {}

        for item_id, item in basket.items():
            if "merchant_id" not in item:
                return JsonResponse({"success": False, "error": f"商品 {item['name']} 缺少商家信息"}, status=400)

            merchant = get_object_or_404(UserProfile, id=item["merchant_id"])

            if merchant not in orders:
                orders[merchant] = Order.objects.create(
                    customer=user,
                    merchant=merchant,
                    status="Ongoing",
                    total_price=Decimal("0.00")
                )

            order = orders[merchant]
            product = get_object_or_404(Item, id=item_id)

            OrderItem.objects.create(
                order=order,
                item=product,
                quantity=item["quantity"]
            )

            order.total_price += Decimal(str(item["price"])) * item["quantity"]
            order.save()

        request.session["basket"] = {}

        return JsonResponse({"success": True, "message": "订单已支付", "order_ids": [order.id for order in orders.values()]})

    except Exception as e:
        print("❌ Checkout 错误:", e)  # ✅ 打印错误日志
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def my_orders(request):
    """ 获取用户的订单（所有状态） """
    orders = Order.objects.filter(
        customer=request.user
    ).order_by('-created_at')

    return render(request, 'user/my_orders.html', {'orders': orders})


@login_required
def add_review(request, order_id):  # ✅ 确保接收 order_id
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    if order.status not in ["Finished", "Canceled"]:
        return JsonResponse({"success": False, "error": "只能对已完成或已取消的订单评价"}, status=400)

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment").strip()

        # 检查是否已经评价过
        if Review.objects.filter(user=request.user, order=order).exists():
            return JsonResponse({"success": False, "error": "您已评价过该订单"}, status=400)

        if not rating or not rating.isdigit() or int(rating) not in range(1, 6):
            return JsonResponse({"success": False, "error": "评分必须在 1-5 之间"}, status=400)

        # 保存评论
        Review.objects.create(
            user=request.user,
            order=order,
            rating=int(rating),
            comment=comment
        )

        return JsonResponse({"success": True, "message": "评价提交成功"})

    return JsonResponse({"success": False, "error": "无效请求"}, status=400)


@login_required
def order_detail(request, order_id):
    # 获取订单并验证用户权限
    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user,  # 确保用户只能查看自己的订单
        status='Finished'        # 仅允许查看已完成订单
    )
    return render(request, 'user/order_detail.html', {'order': order})

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
    """返回当前商家创建的所有类别"""
    if not hasattr(request.user, 'userprofile'):
        print("❌ 该用户没有 userprofile:", request.user)
        return JsonResponse({'error': '未绑定商家信息'}, status=403)

    if not request.user.userprofile.is_merchant:
        print("❌ 该用户不是商家:", request.user)
        return JsonResponse({'error': '无权限访问'}, status=403)

    merchant_profile = request.user.userprofile
    categories = Category.objects.filter(merchant=merchant_profile).values("id", "name")

    print(f"✅ 商家 {merchant_profile.store_name} 的类别数据:", list(categories))
    return JsonResponse({'categories': list(categories)})


@login_required
def add_category(request):
    """ 商家添加新类别 """
    if request.method == "POST":
        if not request.user.userprofile.is_merchant:
            return JsonResponse({'success': False, 'error': '你无权添加类别'}, status=403)

        category_name = request.POST.get("category_name", "").strip()
        merchant = request.user.userprofile  # 绑定商家

        if not category_name:
            return JsonResponse({'success': False, 'error': '类别名称不能为空'}, status=400)

        # 避免重复类别（必须属于当前商家）
        if Category.objects.filter(name=category_name, merchant=merchant).exists():
            return JsonResponse({'success': False, 'error': '该类别已存在'}, status=400)

        try:
            new_category = Category.objects.create(name=category_name, merchant=merchant)
            return JsonResponse({'success': True, 'message': '类别添加成功', 'category': {'id': new_category.id, 'name': new_category.name}})
        except IntegrityError:
            return JsonResponse({'success': False, 'error': '数据库错误，请重试'}, status=500)

    return JsonResponse({'error': '仅支持 POST 请求'}, status=405)


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
    """ 更新商品信息，包括上传图片 """
    if not request.user.userprofile.is_merchant:
        return JsonResponse({"success": False, "error": "无权限访问"}, status=403)

    if request.method == "POST":
        try:
            name = request.POST.get("name")
            price = request.POST.get("price")
            description = request.POST.get("description", "")
            category_id = request.POST.get("category")
            image = request.FILES.get("image")  # 获取上传的图片
            merchant = request.user.userprofile  # 绑定商家

            if not name or not price:
                return JsonResponse({"success": False, "error": "商品名称和价格不能为空！"}, status=400)

            # **判断是更新还是创建**
            if item_id == "new":
                item = Item(
                    name=name,
                    price=Decimal(price),
                    description=description,
                    merchant=merchant,  # **确保商品属于当前商家**
                )
                message = "商品已创建！"
            else:
                item = get_object_or_404(Item, id=item_id, merchant=merchant)
                item.name = name
                item.price = Decimal(price)
                item.description = description
                message = "商品信息已更新！"

            # **更新分类**
            if category_id:
                item.category = get_object_or_404(Category, id=category_id, merchant=merchant)

            # **更新图片（如果用户上传了新图片）**
            if image:
                item.image = image

            item.save()

            return JsonResponse({"success": True, "message": message, "item_id": item.id})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "无效请求"}, status=400)


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

@login_required
def get_reviews(request):
    """ 获取当前商家的用户评论 """
    if not request.user.userprofile.is_merchant:
        return JsonResponse({'error': '无权限访问'}, status=403)

    # 只获取属于该商家的评论
    merchant_profile = request.user.userprofile
    reviews = Review.objects.filter(order__merchant=merchant_profile).order_by('-created_at')

    review_list = [
        {
            "username": review.user.username if review.user else "匿名用户",
            "item": review.order.order_items.first().item.name if review.order.order_items.exists() else "未知商品",
            "order": review.order.order_number if review.order else None,
            "rating": review.rating,
            "comment": review.comment,
            "timestamp": review.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for review in reviews
    ]

    return JsonResponse({"reviews": review_list})