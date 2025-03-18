from django.conf import settings
from django.conf.urls.static import static
from django.urls import path,include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from . import views
from .views import *


urlpatterns = [
      path("login/", auth_views.LoginView.as_view(), name="login"),

      # 用户端
      path("", product_list, name="product_list"),  # 商品列表

      # 商家端
      path("login/", views.login, name="login"),
      path("merchant/", lambda request: redirect("merchant_dashboard")),  # 这里正确重定向
      path("merchant/dashboard/", views.merchant_dashboard, name="merchant_dashboard"),  # ✅ 修正这里
      path("merchant/item_catalog/", views.manage_items, name="manage_items"),
      path("merchant/add_category/", views.add_category, name="add_category"),
      path("merchant/add_item/", views.add_item, name="add_item"),
      path("merchant/edit_item/<int:item_id>/", views.edit_item, name="edit_item"),
      path("merchant/delete_item/<int:item_id>/", views.delete_item, name="delete_item"),
      path("merchant/orders/", views.merchant_orders, name="merchant_orders"),
      path("merchant/orders/update/<int:order_id>/", views.update_order_status, name="update_order_status"),
      path("reviews/", views.view_reviews, name="view_reviews"),
  ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)