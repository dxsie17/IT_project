from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import *


urlpatterns = [
    # 用户端
    path("", product_list, name="product_list"),  # 商品列表
    path("login/", user_login, name="user_login"),  # 登录页面
    path("register/", register, name="register"),  # 注册页面
    path("logout/", user_logout, name="logout"),  # 退出登录
    path("users/<slug:store_slug>/", users_takeorder, name="users_takeorder"),
    path("select-store/", select_store, name="select_store"),
    path("item/<int:item_id>/", item_detail, name="item_detail"),  # 商品详情
    path("add-to-basket/<int:item_id>/", add_to_basket, name="add_to_basket"),  # 添加到购物车
    path("get-cart/", get_cart, name="get_cart"),  # 获取购物车
    path("decrease-from-basket/<int:item_id>/", decrease_from_basket, name="decrease_from_basket"),  # 减少购物车商品
    path("remove-from-basket/<int:item_id>/", remove_from_basket, name="remove_from_basket"),  # 移除购物车商品
    path("checkout/", checkout, name="checkout"),
    path("my_orders/", my_orders, name="my_orders"),  # 我的订单页面
    path("add-review/<int:order_id>/", add_review, name="add_review"),  # 添加评论

    # 商家端
    path("merchant/", merchant_dashboard, name="merchant_dashboard"),  # 商家后台
    path("merchant/items/", manage_items, name="manage_items"),  # 商品管理
    path("merchant/category/add/", add_category, name="add_category"),  # 添加商品类别
    path("merchant/categories/", get_categories, name="get_categories"),  # 获取商品类别
    path("merchant/manage_items/", manage_items, name="manage_items"),
    path("merchant/item/edit/<int:item_id>/", edit_item, name="edit_item"),  # 编辑商品
    path("merchant/item/details/<int:item_id>/", item_details, name="item_details"),  # 商品信息
    path("merchant/item/toggle/<int:item_id>/", toggle_item_availability, name="toggle_item_availability"),  # 上下架商品
    re_path(r"^merchant/item/update/(?P<item_id>\d+|new)/$", update_item, name="update_item"),  # 更新商品
    path("merchant/item/delete/<int:item_id>/", delete_item, name="delete_item"),  # 删除商品
    path("merchant/orders/", merchant_orders, name="merchant_orders"),  # 商家订单管理
    path("merchant/orders/update/<int:order_id>/", update_order_status, name="update_order_status"),  # 修改订单状态
    path("merchant/reviews/", get_reviews, name="get_reviews"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)