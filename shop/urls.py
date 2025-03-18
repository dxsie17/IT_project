from django.urls import path
from .views import *
from shop import views


urlpatterns = [
    
    path("", product_list, name="product_list"), # 商品列表
    path('logout/', custom_logout, name='logout'),
    path("login/", login, name="login"),  # 登录页面
    path("register/", register, name="register"),  # 注册页面
    # path("checkout/", checkout, name="checkout"),  # 结算下单
    # path("order/pay/<int:order_id>/", pay_order, name="pay_order"),  # 订单支付
    # path("my_orders/", my_orders, name="my_orders"),  # 我的订单
    # path("review/add/<int:item_id>/", add_review, name="add_review"),  # 订单评价

    # 用户端
    path("users/",users_takeorder, name="users_takeorder"),
    path('item/<int:item_id>/', item_detail, name='item_detail'),
    path('add-to-basket/<int:item_id>/', add_to_basket, name='add_to_basket'),
    path('get-cart/', get_cart, name='get_cart'),
    path('decrease-from-basket/<int:item_id>/', decrease_from_basket, name='decrease_from_basket'),
    path('remove-from-basket/<int:item_id>/', remove_from_basket, name='remove_from_basket'),

    # 商家端
    path("merchant/", merchant_dashboard, name="merchant_dashboard"),  # 商家后台
    path("merchant/item_catalog/", manage_items, name="manage_items"), # 商品管理
    path("merchant/add_category/", add_category, name="add_category"), # 添加商品类别
    path("merchant/add_item/", add_or_edit_item, name="add_item"), # 添加商品
    path("merchant/edit_item/<int:item_id>/", edit_item, name="edit_item"), # 编辑商品
    path("merchant/delete_item/<int:item_id>/", delete_item, name="delete_item"), # 删除商品
    path("merchant/orders/", merchant_orders, name="merchant_orders"),  # 商家订单管理
    path("merchant/orders/update/<int:order_id>/", update_order_status, name="update_order_status"),  # 修改订单状态
]