
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Item, Order, OrderItem, Review, UserProfile, Merchant, Category


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
        return render(request,"login.html")
    else:
        #print(request.POST)
        username = request.POST.get("user")
        password = request.POST.get("password")

        if username == "user" and password == "123":
            return render(request,"list.html")
        else:
            return render(request,"login.html", {"error_msg":"Error!"})


""""
商家端
"""
"""商家后台"""
@login_required
def merchant_dashboard(request):
    try:
        if not request.user.userprofile.is_merchant:
            return redirect("/")  # 不是商家跳转到首页
        merchant = request.user.merchant  # 确保 `Merchant` 存在
    except (UserProfile.DoesNotExist, Merchant.DoesNotExist):
        return redirect("/")  # 没有 `UserProfile` 或 `Merchant` 记录的用户跳转首页

    items = Item.objects.filter(merchant=merchant)
    return render(request, "merchant/dashboard.html", {"items": items})

"""商品管理"""
@login_required
def manage_items(request):
    items = Item.objects.filter(merchant=request.user)
    categories = Category.objects.all()
    return render(request, "merchant/item_catalog.html", {"items": items})

"""添加商品类别"""
@login_required
def add_category(request):
    if request.method == "POST":
        name = request.POST.get("category_name")
        is_addon = request.POST.get("is_addon") == "yes"
        Category.objects.create(name=name, is_addon=is_addon)
        return redirect("merchant/manage_items")

"""商家添加、编辑商品"""
@login_required
def add_or_edit_item(request):
    merchant = request.user.merchant  # 确保用户是商家
    categories = Category.objects.all()  # 获取所有类别

    if request.method == "POST":
        item_id = request.POST.get("item_id")
        name = request.POST.get("name")
        category_id = request.POST.get("category_id")
        price = request.POST.get("price")
        image = request.FILES.get("image")

        category = get_object_or_404(Category, id=category_id)

        if item_id:  # 编辑商品
            item = get_object_or_404(Item, id=item_id, merchant=merchant)
            item.name = name
            item.category = category
            item.price = price
            if image:
                item.image = image
            item.save()
        else:  # 新增商品
            Item.objects.create(name=name, category=category, price=price, image=image, merchant=merchant)

        return redirect("manage_items")

    return render(request, "merchant/manage_items.html", {"categories": categories})

"""删除商品"""
@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, merchant=request.user)
    item.delete()
    return redirect("merchant_item_catalog")

"""获取商品详情（用于前端 JS 进行编辑）"""
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return JsonResponse({"id": item.id, "name": item.name, "category_id": item.category.id, "price": str(item.price)})

"""商家管理订单"""
@login_required
def merchant_orders(request):
    if not hasattr(request.user, "userprofile") or not request.user.userprofile.is_merchant:
        return redirect("/")  # 非商家无法访问

    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "Ongoing")

    # 只获取该商家名下的订单
    orders = Order.objects.filter(items__merchant__user=request.user, status=status_filter).distinct()

    # 应用搜索过滤条件
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(items__name__icontains=search_query)
        ).distinct()

    return render(request, "merchant/orders.html", {"orders": orders, "status_filter": status_filter})


"""商家修改订单状态"""
@login_required
def update_order_status(request, order_id):
    if not hasattr(request.user, "userprofile") or not request.user.userprofile.is_merchant:
        return redirect("/")

    order = get_object_or_404(Order, id=order_id, items__merchant__user=request.user)

    if request.method == "POST":
        new_status = request.POST.get("status", "")
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()

    return redirect("merchant_orders")