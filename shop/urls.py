from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import *

urlpatterns = [
    # User side
    # path("", product_list, name="product_list"),  # Product list
    path("login/", user_login, name="user_login"),  # Login page
    path("register/", register, name="register"),  # Registration page
    path("logout/", user_logout, name="logout"),  # Logout
    path("users/<slug:store_slug>/", users_takeorder, name="users_takeorder"),  # User order placement
    path("select-store/", select_store, name="select_store"),  # Select a store
    path("item/<int:item_id>/", item_detail, name="item_detail"),  # Product details
    path("add-to-basket/<int:item_id>/", add_to_basket, name="add_to_basket"),  # Add to cart
    path("get-cart/", get_cart, name="get_cart"),  # Retrieve cart contents
    path("decrease-from-basket/<int:item_id>/", decrease_from_basket, name="decrease_from_basket"),  # Reduce item quantity in cart
    path("remove-from-basket/<int:item_id>/", remove_from_basket, name="remove_from_basket"),  # Remove item from cart
    path("checkout/", checkout, name="checkout"),  # Checkout
    path("my_orders/", my_orders, name="my_orders"),  # My orders page
    path("add-review/<int:order_id>/", add_review, name="add_review"),  # Add a review

    # Merchant side
    path("merchant/", merchant_dashboard, name="merchant_dashboard"),  # Merchant dashboard
    path("merchant/items/", manage_items, name="manage_items"),  # Manage products
    path("merchant/category/add/", add_category, name="add_category"),  # Add product category
    path("merchant/categories/", get_categories, name="get_categories"),  # Retrieve product categories
    path("merchant/manage_items/", manage_items, name="manage_items"),  # Manage items
    path("merchant/item/edit/<int:item_id>/", edit_item, name="edit_item"),  # Edit product
    path("merchant/item/details/<int:item_id>/", item_details, name="item_details"),  # Product details
    path("merchant/item/toggle/<int:item_id>/", toggle_item_availability, name="toggle_item_availability"),  # Toggle product availability
    re_path(r"^merchant/item/update/(?P<item_id>\d+|new)/$", update_item, name="update_item"),  # Update product
    path("merchant/item/delete/<int:item_id>/", delete_item, name="delete_item"),  # Delete product
    path("merchant/orders/", merchant_orders, name="merchant_orders"),  # Merchant order management
    path("merchant/orders/update/<int:order_id>/", update_order_status, name="update_order_status"),  # Update order status
    path("merchant/reviews/", get_reviews, name="get_reviews"),  # Retrieve reviews
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)