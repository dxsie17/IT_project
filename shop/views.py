
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Item, Order, OrderItem, Review, UserProfile, Merchant, Category
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

"""
用户端
"""
# 商品列表
def product_list(request):
    return render(request, "home.html")

def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        next_url = request.GET.get("next")  # 获取 'next' 参数

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)

            # 获取用户扩展信息
            user_profile = UserProfile.objects.get(user=user)

            # # 根据角色跳转
            # if user_profile.is_merchant:
            #     return redirect("merchant_dashboard")  # 商家端
            # else:
            #     return redirect("users_takeorder")  # 用户端
            try:
                profile = user.userprofile
                print(f"用户角色: 商家={profile.is_merchant}")
                if profile.is_merchant:
                    print("尝试跳转到商家仪表盘")
                    return redirect("merchant_dashboard")
                else:
                    print("跳转到用户端")
                    return redirect("users_takeorder")
            except UserProfile.DoesNotExist:
                print("用户资料不存在")
                return redirect("product_list")
        else:
            return render(request, "login.html", {"error": "用户名或密码错误"})

    return render(request, "login.html")

def register(request):
    if request.method == "POST":
        email = request.POST["email"]
        phone = request.POST["phone"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]
        is_merchant = request.POST.get("is_merchant", "off") == "on"  # 是否是商家

        # 确保密码一致
        if password1 != password2:
            return render(request, "registration/register.html", {"error": "Passwords do not match"})

        # 确保 Email 没有被注册
        if User.objects.filter(email=email).exists():
            return render(request, "registration/register.html", {"error": "Email already registered"})
        
        # 避免重复的用户名
        if User.objects.filter(username=email).exists():
            return render(request, "registration/register.html", {"error": "Email already registered"})
        
        # 创建 User 并保存
        user = User.objects.create_user(username=email, email=email, password=password1)
        user.save()

        # 创建 UserProfile 绑定 User
        user_profile = UserProfile.objects.create(user=user, is_merchant=is_merchant)
        user_profile.save()
        #print("UserProfile saved:", user_profile)

        # 如果是商家，创建 Merchant 记录
        if is_merchant:
            Merchant.objects.create(
                user=user,  # 使用已保存的 user 实例
                store_name=f"{user.username}'s Store"
            )
            print(f"商家记录已创建：{user.username}")

        # 认证并登录
        user = authenticate(username=email, password=password1)
        if user:
            auth_login(request, user)
            return redirect("login")  # 登录后跳转主页

    return render(request, "registration/register.html")

def custom_logout(request):
    logout(request)
    return redirect('product_list')

###user端
@login_required
def users_takeorder(request):
    #return render(request, "user/takeorder.html")
    
    # 获取所有分类
    categories = Category.objects.all()
    
    # 默认显示第一个分类的商品
    default_category = categories.first()
    items = Item.objects.filter(category=default_category, is_available=True)
    
    # 处理分类筛选
    selected_category = request.GET.get('category')
    if selected_category:
        items = Item.objects.filter(category__name=selected_category, is_available=True)
    
    return render(request, "user/takeorder.html", {
        'categories': categories,
        'items': items,
        'selected_category': selected_category
    })

@login_required
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return render(request, "user/item_detail.html", {'item': item})

@login_required
def add_to_basket(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    
    # 获取或创建进行中的订单
    order, created = Order.objects.get_or_create(
        customer=request.user,
        status='Ongoing',
        defaults={'total_price': 0}
    )
    
    # 添加或更新订单项
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
def get_cart(request):
    order = Order.objects.filter(customer=request.user, status='Ongoing').first()
    cart_items = []
    if order:
        cart_items = [{
            'id': oi.item.id,  # 新增商品ID
            'name': oi.item.name,
            'quantity': oi.quantity,
            'unit_price': str(oi.item.price),  # 新增单价
            'total_price': str(oi.item.price * oi.quantity)
        } for oi in order.orderitem_set.all()]
    return JsonResponse({'items': cart_items})

@login_required
def decrease_from_basket(request, item_id):
    # 获取目标商品和订单
    item = get_object_or_404(Item, id=item_id)
    order = get_object_or_404(Order, customer=request.user, status='Ongoing')
    
    try:
        # 获取订单项并操作
        order_item = OrderItem.objects.get(order=order, item=item)
        if order_item.quantity > 1:
            order_item.quantity -= 1
            order_item.save()
        else:
            order_item.delete()
        return JsonResponse({'success': True})
    except OrderItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': '商品不在购物车中'}, status=400)

@login_required
def remove_from_basket(request, item_id):
    # 获取目标商品和订单
    item = get_object_or_404(Item, id=item_id)
    order = get_object_or_404(Order, customer=request.user, status='Ongoing')
    
    try:
        # 直接删除订单项
        order_item = OrderItem.objects.get(order=order, item=item)
        order_item.delete()
        return JsonResponse({'success': True})
    except OrderItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': '商品不在购物车中'}, status=400)
""""
商家端
"""
"""商家后台"""
@login_required
def merchant_dashboard(request):
    try:
        # 验证用户资料存在
        user_profile = request.user.userprofile
        
        # 检查商家标识
        if not user_profile.is_merchant:
            return redirect("product_list")
        
        # 获取商家信息（确保存在）
        merchant = Merchant.objects.get(user=request.user)
        
        # 获取商家商品
        items = Item.objects.filter(merchant=merchant)
        
    except (UserProfile.DoesNotExist, Merchant.DoesNotExist):
        # 记录错误日志
        print(f"商家信息缺失: {request.user}")
        return redirect("product_list")
    
    return render(request, "merchant/dashboard.html", {"items": items})
    # try:
    #     if not request.user.userprofile.is_merchant:
    #         return redirect("/")  # 不是商家跳转到首页
    #     merchant = request.user.merchant  # 确保 `Merchant` 存在
    # except (UserProfile.DoesNotExist, Merchant.DoesNotExist):
    #     return redirect("/")  # 没有 `UserProfile` 或 `Merchant` 记录的用户跳转首页

    # items = Item.objects.filter(merchant=merchant)
    # return render(request, "merchant/dashboard.html", {"items": items})
    

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