from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.db.models import Q
from .models import Item, Order, OrderItem, Review, UserProfile, Merchant, Category
import json


"""
用户端
"""
# 商品列表
def product_list(request):
    items = Item.objects.all()
    return render(request, "list.html", {"items": items})

# 用户登录
def login(request):
    if request.method == "GET":
        return render(request, "login.html")
    else:
        username = request.POST.get("user")
        password = request.POST.get("password")

        if username == "user" and password == "123":
            return render(request, "list.html")
        else:
            return render(request, "login.html", {"error_msg": "Error!"})


""""
商家端
"""
"""商家后台"""
@login_required
def merchant_dashboard(request):
    user = request.user
    print(f"🛠️ 当前用户: {user.username}")

    # 订单状态筛选
    status_filter = request.GET.get("status", "Ongoing")
    print(f"🛠️ 当前订单筛选状态: {status_filter}")

    if user.is_superuser:
        print("✅ 超管访问商家后台")
        items = Item.objects.all()
        orders = Order.objects.filter(status=status_filter)
        categories = Category.objects.all()
        reviews = Review.objects.all()
    else:
        if not hasattr(user, "userprofile") or not user.userprofile.is_merchant:
            print("❌ 用户不是商家，跳转到首页")
            return redirect("/")

        merchant = user.merchant
        orders = Order.objects.filter(items__merchant=merchant, status=status_filter).distinct()
        items = Item.objects.filter(merchant=merchant)
        categories = Category.objects.all()
        reviews = Review.objects.filter(merchant=merchant)

    return render(request, "merchant/dashboard.html", {
        "items": items,
        "orders": orders,
        "categories": categories,
        "reviews": reviews
    })



"""📌 新增：提供 AJAX 订单筛选 API"""
@login_required
def get_orders_by_status(request, status):
    """前端 AJAX 请求不同状态的订单"""
    user = request.user
    if not hasattr(user, "userprofile") or not user.userprofile.is_merchant:
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    merchant = user.merchant
    orders = Order.objects.filter(items__merchant=merchant, status=status).distinct()

    orders_data = []
    for order in orders:
        orders_data.append({
            "order_number": order.order_number,
            "status": order.status,
            "customer": order.customer.username,
            "total_price": order.total_price,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
            "items": [
                {
                    "name": item.product.name,
                    "image": item.product.image.url if item.product.image else "",
                    "price": item.product.price,
                    "quantity": item.quantity
                }
                for item in order.orderitem_set.all()
            ]
        })

    return JsonResponse({"success": True, "orders": orders_data})



"""商品管理"""
@login_required
def manage_items(request):
    if not request.user.is_superuser and (not hasattr(request.user, "userprofile") or not request.user.userprofile.is_merchant):
        return redirect("/")

    items = Item.objects.all()
    return render(request, "merchant/item_catalog.html", {"items": items})


"""添加商品类别"""
@login_required
def add_category(request):
    if request.method == "POST":
        category_name = request.POST.get("category_name")
        if category_name:
            Category.objects.create(name=category_name)
            return redirect("manage_items")


"""商家添加商品"""
@login_required
def add_item(request):
    if request.method == "POST":
        name = request.POST.get("name")
        price = request.POST.get("price")
        category_id = request.POST.get("category_id")

        category = get_object_or_404(Category, id=category_id)
        Item.objects.create(name=name, price=price, category=category)
        return redirect("manage_items")

    return render(request, "merchant/add_item.html")
"""商家编辑商品"""
@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        item.name = request.POST.get("name", item.name)
        item.price = request.POST.get("price", item.price)
        item.save()
        return redirect("manage_items")

    return render(request, "merchant/edit_item.html", {"item": item})

"""删除商品"""
@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    item.delete()
    return redirect("manage_items")


"""商家管理订单"""
@login_required
def merchant_orders(request):
    if not request.user.is_superuser and (not hasattr(request.user, "userprofile") or not request.user.userprofile.is_merchant):
        return redirect("/")

    status_filter = request.GET.get("status", "Ongoing")
    orders = Order.objects.filter(status=status_filter)

    return render(request, "merchant/orders.html", {"orders": orders})

"""商家修改订单状态"""
@csrf_protect
@login_required
def update_order_status(request, order_id):
    expected_csrf_token = get_token(request)
    received_csrf_token = request.headers.get("X-CSRFToken", "")

    print(f"🛠️ Received CSRF Token: {received_csrf_token}")
    print(f"🛠️ Expected CSRF Token: {expected_csrf_token}")

    if received_csrf_token != expected_csrf_token:
        return JsonResponse({"success": False, "error": "CSRF token mismatch"}, status=403)

    if not hasattr(request.user, "userprofile") or not request.user.userprofile.is_merchant:
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_status = data.get("status")

            if new_status in [choice[0] for choice in Order.STATUS_CHOICES]:
                order.status = new_status
                order.save()
                return JsonResponse({"success": True, "new_status": new_status})

            return JsonResponse({"success": False, "error": "Invalid status"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)


""" 查看用户评价 """
@login_required
def view_reviews(request):
    reviews = Review.objects.all()
    return render(request, "merchant/reviews.html", {"reviews": reviews})