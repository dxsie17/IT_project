import json
import traceback
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Item, Order, OrderItem, Review, UserProfile, Category, generate_unique_order_number
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt


"""User Side"""
# Product list
def product_list(request):
    return redirect("user_login")

# Merchant/User login
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Check if username exists
        user = User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({"success": False, "error": "User does not exist, please check username or register"}, status=400)

        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse({"success": False, "error": "Incorrect password, please try again"}, status=400)

        auth_login(request, user)
        user_profile = getattr(user, "userprofile", None)

        # Redirect merchants to their store
        if user_profile and user_profile.is_merchant:
            return JsonResponse({"success": True, "redirect_url": "/merchant/"})

        # Redirect regular users to store selection page
        return JsonResponse({"success": True, "redirect_url": "/select-store/"})

    return render(request, "login.html")


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        phone = request.POST.get("phone")  # Fixed field name
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        is_merchant = request.POST.get("is_merchant") == "on"  # Get checkbox status
        store_name = request.POST.get("store_name") if is_merchant else None

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect("register")

        # Merchant must provide a store name
        if is_merchant:
            if not store_name or len(store_name.strip()) < 2:
                messages.error(request, "Merchants must provide a valid store name (at least 2 characters).")
                return redirect("register")
            if UserProfile.objects.filter(store_name=store_name).exists():
                messages.error(request, "Store name already exists.")
                return redirect("register")
        try:
            # Create User
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password1
            )
            user.save()

            # Associate UserProfile
            user_profile = UserProfile.objects.create(
                user=user,
                phone_number=phone,
                is_merchant=is_merchant,
                store_name=store_name
            )
            user_profile.save()

            auth_login(request, user)  # Auto-login after registration
            if user_profile.is_merchant:
                messages.success(request, "Merchant registration successful!")
                return redirect("user_login")
            else:
                messages.success(request, "Registration successful!")
                return redirect("user_login")

        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect("register")

    return render(request, "register.html")


def user_logout(request):
	logout(request)
	return redirect('user_login')

@login_required
def select_store(request):
    """ Display all merchant stores for user selection """
    merchants = UserProfile.objects.filter(is_merchant=True).values("store_name", "store_slug")
    print("🔍 Merchant data:", list(merchants))
    return render(request, "user/select_store.html", {"merchants": merchants})

### User Side
@login_required
def users_takeorder(request, store_slug):
    # Get the merchant
    merchant = get_object_or_404(UserProfile, store_slug=store_slug, is_merchant=True)
    # Retrieve only this merchant's categories
    categories = Category.objects.filter(merchant=merchant)
    default_category = categories.first()
    # Retrieve only this merchant's products
    items = Item.objects.filter(merchant=merchant, category=default_category, is_available=True)

    selected_category = request.GET.get('category')
    if selected_category:
        items = Item.objects.filter(merchant=merchant, category__name=selected_category, is_available=True)

    return render(request, "user/takeorder.html", {
        'categories': categories,
        'items': items,
        'selected_category': selected_category,
        'merchant': merchant,  # Pass merchant information
    })

### Fetch product details
@login_required
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return JsonResponse({
        "id": item.id,
        "name": item.name,
        "price": float(item.price),  # Convert Decimal type
        "description": item.description,
        "image": item.image.url if item.image else None
    })

### Add to cart
@login_required
def add_to_basket(request, item_id):
    """ Add product to shopping cart """
    try:
        item = get_object_or_404(Item, id=item_id)

        # ✅ Get merchant ID
        merchant_id = item.merchant.id if item.merchant else None
        if not merchant_id:
            return JsonResponse({"success": False, "error": "Product not linked to a merchant"}, status=400)

        basket = request.session.get("basket", {})

        if str(item_id) in basket:
            basket[str(item_id)]["quantity"] += 1
        else:
            basket[str(item_id)] = {
                "name": item.name,
                "price": float(item.price),
                "quantity": 1,
                "merchant_id": merchant_id  # ✅ Save merchant ID
            }

        request.session["basket"] = basket
        request.session.modified = True  # ✅ Force save session
        return JsonResponse({"success": True, "message": "Product added to cart"})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def decrease_from_basket(request, item_id):
    """ Reduce quantity of a product in the cart """
    basket = request.session.get("basket", {})

    if str(item_id) in basket:
        if basket[str(item_id)]["quantity"] > 1:
            basket[str(item_id)]["quantity"] -= 1
        else:
            del basket[str(item_id)]  # Remove product when quantity is 0

    request.session["basket"] = basket
    return JsonResponse({"success": True, "message": "Product quantity updated"})


@login_required
def remove_from_basket(request, item_id):
    """ Remove product from cart """
    basket = request.session.get("basket", {})

    if str(item_id) in basket:
        del basket[str(item_id)]

    request.session["basket"] = basket
    return JsonResponse({"success": True, "message": "Product removed"})


@login_required
def get_cart(request):
    """ Retrieve shopping cart contents and total price """
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
    """ Generate orders after user payment """
    try:
        basket = request.session.get("basket", {})

        if not basket:
            return JsonResponse({"success": False, "error": "The cart is empty"}, status=400)

        user = request.user
        orders = {}

        with transaction.atomic():  # ✅ 开启事务，确保数据一致性
            for item_id, item in basket.items():
                merchant = UserProfile.objects.filter(id=item["merchant_id"]).first()
                if not merchant:
                    return JsonResponse({"success": False, "error": f"Merchant ID {item['merchant_id']} not found"}, status=400)

                # ✅ 生成唯一订单号
                order_number = generate_unique_order_number()

                order = Order.objects.create(
                    order_number=order_number,
                    customer=user,
                    merchant=merchant,
                    status="Ongoing",
                    total_price=Decimal("0.00")
                )

                product = get_object_or_404(Item, id=item_id)
                OrderItem.objects.create(order=order, item=product, quantity=item["quantity"])
                order.total_price += Decimal(str(item["price"])) * item["quantity"]
                order.save()

                orders[merchant] = order

            request.session["basket"] = {}

        return JsonResponse({"success": True, "message": "Order successfully placed", "order_ids": [order.id for order in orders.values()]})

    except IntegrityError as e:
        print("❌ Checkout Error: Order number conflict", e)
        return JsonResponse({"success": False, "error": "Order number conflict, please try again"}, status=500)


@login_required
def my_orders(request):
    """ Retrieve user's orders (all statuses) """
    orders = Order.objects.filter(
        customer=request.user
    ).order_by('-created_at')

    return render(request, 'user/my_orders.html', {'orders': orders})


@login_required
def add_review(request, order_id):  # ✅ Ensure order_id is received
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    if order.status not in ["Finished", "Canceled"]:
        return JsonResponse({"success": False, "error": "You can only review completed or canceled orders"}, status=400)

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment").strip()

        # Check if the order has already been reviewed
        if Review.objects.filter(user=request.user, order=order).exists():
            return JsonResponse({"success": False, "error": "You have already reviewed this order"}, status=400)

        if not rating or not rating.isdigit() or int(rating) not in range(1, 6):
            return JsonResponse({"success": False, "error": "Rating must be between 1 and 5"}, status=400)

        # Save the review
        Review.objects.create(
            user=request.user,
            order=order,
            rating=int(rating),
            comment=comment
        )

        return JsonResponse({"success": True, "message": "Review submitted successfully"})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@login_required
def order_detail(request, order_id):
    """ Retrieve order details and verify user permission """
    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user,  # Ensure users can only view their own orders
        status='Finished'        # Only allow viewing completed orders
    )
    return render(request, 'user/order_detail.html', {'order': order})

"""
Merchant Side
"""

@login_required
def merchant_dashboard(request):
    """ Merchant dashboard """
    try:
        user_profile = request.user.userprofile
        if not user_profile.is_merchant:
            return redirect("product_list")

        # Read query parameters, default to displaying ongoing orders
        status_filter = request.GET.get("status", "Ongoing")

        # Retrieve only the merchant's orders
        orders = Order.objects.filter(merchant=user_profile, status=status_filter).prefetch_related("order_items__item")

        # Retrieve all products of the merchant
        items = Item.objects.filter(merchant=user_profile)

        # Get merchant store name
        store_name = user_profile.store_name  # Ensure UserProfile or Merchant model contains `store_name` field

    except UserProfile.DoesNotExist:
        return redirect("product_list")

    return render(request, "merchant/dashboard.html", {
        "orders": orders,
        "items": items,
        "status_filter": status_filter,
        "store_name": store_name  # Pass store_name
    })


@login_required
def item_details(request, item_id):
    """ Get product details """
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
        return JsonResponse({"error": "Product does not exist"}, status=404)


@login_required
def manage_items(request):
    """ Merchant manages products (returns JSON data) """
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
            "category": item.category.name if item.category else "Uncategorized",
        }
        for item in items
    ]

    return JsonResponse({"items": items_data})


@login_required
def get_categories(request):
    """ Return all categories created by the current merchant """
    if not hasattr(request.user, 'userprofile'):
        print("❌ User does not have a userprofile:", request.user)
        return JsonResponse({'error': 'Merchant information not linked'}, status=403)

    if not request.user.userprofile.is_merchant:
        print("❌ User is not a merchant:", request.user)
        return JsonResponse({'error': 'Unauthorized access'}, status=403)

    merchant_profile = request.user.userprofile
    categories = Category.objects.filter(merchant=merchant_profile).values("id", "name")

    print(f"✅ Categories data for merchant {merchant_profile.store_name}:", list(categories))
    return JsonResponse({'categories': list(categories)})


@login_required
def add_category(request):
    """ Merchant adds a new category """
    if request.method == "POST":
        if not request.user.userprofile.is_merchant:
            return JsonResponse({'success': False, 'error': 'You are not authorized to add categories'}, status=403)

        category_name = request.POST.get("category_name", "").strip()
        merchant = request.user.userprofile  # Bind to merchant

        if not category_name:
            return JsonResponse({'success': False, 'error': 'Category name cannot be empty'}, status=400)

        # Avoid duplicate categories (must belong to the current merchant)
        if Category.objects.filter(name=category_name, merchant=merchant).exists():
            return JsonResponse({'success': False, 'error': 'This category already exists'}, status=400)

        try:
            new_category = Category.objects.create(name=category_name, merchant=merchant)
            return JsonResponse({'success': True, 'message': 'Category added successfully', 'category': {'id': new_category.id, 'name': new_category.name}})
        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Database error, please try again'}, status=500)

    return JsonResponse({'error': 'Only POST requests are supported'}, status=405)


@login_required
def add_item(request):
    """ Merchant adds a new product """
    if not request.user.userprofile.is_merchant:
        return redirect("product_list")

    categories = Category.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category_id")
        price = request.POST.get("price")
        image = request.FILES.get("image")

        category = get_object_or_404(Category, id=category_id)

        # Create product
        Item.objects.create(
            name=name,
            category=category,
            price=price,
            image=image,
            merchant=request.user.userprofile,
            is_available=True,  # Default to available
        )
        return redirect("manage_items")

    return render(request, "merchant/add_item.html", {"categories": categories})


@login_required
def toggle_item_availability(request, item_id):
    """ Toggle product availability (list/unlist) """
    item = get_object_or_404(Item, id=item_id, merchant=request.user.userprofile)

    # Toggle product availability status
    item.is_available = not item.is_available
    item.save()

    return JsonResponse({"success": True, "new_status": item.is_available})


@login_required
def edit_item(request, item_id):
    """ Merchant edits an existing product """
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
    """ Delete product (only merchant can perform this action) """
    item = get_object_or_404(Item, id=item_id)

    if item.merchant != request.user.userprofile:
        return JsonResponse({'success': False, 'error': 'You are not authorized to delete this product'}, status=403)

    # Check if the product is still in any orders
    if OrderItem.objects.filter(item=item).exists():
        return JsonResponse({'success': False, 'error': 'Cannot delete, this product is still in orders'}, status=400)

    item.delete()
    return JsonResponse({'success': True, 'message': 'Product deleted successfully'})


@login_required
def update_item(request, item_id):
    """ Update product information, including uploading an image """
    if not request.user.userprofile.is_merchant:
        return JsonResponse({"success": False, "error": "Unauthorized access"}, status=403)

    if request.method == "POST":
        try:
            name = request.POST.get("name")
            price = request.POST.get("price")
            description = request.POST.get("description", "")
            category_id = request.POST.get("category")
            image = request.FILES.get("image")  # Retrieve the uploaded image
            merchant = request.user.userprofile  # Bind to the merchant

            if not name or not price:
                return JsonResponse({"success": False, "error": "Product name and price cannot be empty!"}, status=400)

            # **Determine whether it's an update or a new creation**
            if item_id == "new":
                item = Item(
                    name=name,
                    price=Decimal(price),
                    description=description,
                    merchant=merchant,  # **Ensure the product belongs to the current merchant**
                )
                message = "Product created!"
            else:
                item = get_object_or_404(Item, id=item_id, merchant=merchant)
                item.name = name
                item.price = Decimal(price)
                item.description = description
                message = "Product information updated!"

            # **Update category**
            if category_id:
                item.category = get_object_or_404(Category, id=category_id, merchant=merchant)

            # **Update image (if the user uploaded a new one)**
            if image:
                item.image = image

            item.save()

            return JsonResponse({"success": True, "message": message, "item_id": item.id})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@login_required
def merchant_orders(request):
    """ Merchant manages orders """
    if not request.user.userprofile.is_merchant:
        return redirect("/")

    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "Ongoing")

    # Directly fetch orders related to the merchant
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
    """ Merchant updates order status """
    if not request.user.userprofile.is_merchant:
        return JsonResponse({'error': 'Unauthorized access'}, status=403)

    order = get_object_or_404(Order, id=order_id)

    # Only allow modifying orders that contain the merchant's products
    merchant_items_in_order = OrderItem.objects.filter(
        order=order, item__merchant=request.user.userprofile
    ).exists()

    if not merchant_items_in_order:
        return JsonResponse({'error': 'You are not authorized to modify this order'}, status=403)

    if request.method == "POST":
        new_status = request.POST.get("status", "")
        valid_statuses = [s[0] for s in Order.status_choices]

        if new_status in valid_statuses:
            order.status = new_status
            order.save()
            return JsonResponse({'success': True, 'message': 'Order status updated'})

        return JsonResponse({'error': 'Invalid order status'}, status=400)

    return JsonResponse({'error': 'Request error'}, status=400)

@login_required
def get_reviews(request):
    """ Retrieve user reviews for the current merchant """
    if not request.user.userprofile.is_merchant:
        return JsonResponse({'error': 'Unauthorized access'}, status=403)

    # Fetch only reviews related to the current merchant
    merchant_profile = request.user.userprofile
    reviews = Review.objects.filter(order__merchant=merchant_profile).order_by('-created_at')

    review_list = [
        {
            "username": review.user.username if review.user else "Anonymous User",
            "item": review.order.order_items.first().item.name if review.order.order_items.exists() else "Unknown Product",
            "order": review.order.order_number if review.order else None,
            "rating": review.rating,
            "comment": review.comment,
            "timestamp": review.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for review in reviews
    ]

    return JsonResponse({"reviews": review_list})