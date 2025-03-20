from django.test import SimpleTestCase
from django.urls import reverse, resolve
from shop.views import (
    user_login, register, user_logout, users_takeorder, select_store,
    item_detail, add_to_basket, get_cart, decrease_from_basket, remove_from_basket,
    checkout, my_orders, add_review, merchant_dashboard, manage_items, add_category,
    get_categories, edit_item, item_details, toggle_item_availability, update_item,
    delete_item, merchant_orders, update_order_status, get_reviews
)

class TestUrls(SimpleTestCase):

    def test_login_url_resolves(self):
        """ Test if the login URL resolves correctly """
        url = reverse("user_login")
        self.assertEqual(resolve(url).func, user_login)

    def test_register_url_resolves(self):
        """ Test if the registration URL resolves correctly """
        url = reverse("register")
        self.assertEqual(resolve(url).func, register)

    def test_logout_url_resolves(self):
        """ Test if the logout URL resolves correctly """
        url = reverse("logout")
        self.assertEqual(resolve(url).func, user_logout)

    def test_users_takeorder_url_resolves(self):
        """ Test if the user order page URL resolves correctly """
        url = reverse("users_takeorder", args=["test-store"])
        self.assertEqual(resolve(url).func, users_takeorder)

    def test_select_store_url_resolves(self):
        """ Test if the store selection page URL resolves correctly """
        url = reverse("select_store")
        self.assertEqual(resolve(url).func, select_store)

    def test_item_detail_url_resolves(self):
        """ Test if the product details page URL resolves correctly """
        url = reverse("item_detail", args=[1])
        self.assertEqual(resolve(url).func, item_detail)

    def test_add_to_basket_url_resolves(self):
        """ Test if the add to cart URL resolves correctly """
        url = reverse("add_to_basket", args=[1])
        self.assertEqual(resolve(url).func, add_to_basket)

    def test_get_cart_url_resolves(self):
        """ Test if the get cart URL resolves correctly """
        url = reverse("get_cart")
        self.assertEqual(resolve(url).func, get_cart)

    def test_decrease_from_basket_url_resolves(self):
        """ Test if the decrease quantity in cart URL resolves correctly """
        url = reverse("decrease_from_basket", args=[1])
        self.assertEqual(resolve(url).func, decrease_from_basket)

    def test_remove_from_basket_url_resolves(self):
        """ Test if the remove item from cart URL resolves correctly """
        url = reverse("remove_from_basket", args=[1])
        self.assertEqual(resolve(url).func, remove_from_basket)

    def test_checkout_url_resolves(self):
        """ Test if the checkout URL resolves correctly """
        url = reverse("checkout")
        self.assertEqual(resolve(url).func, checkout)

    def test_my_orders_url_resolves(self):
        """ Test if the my orders page URL resolves correctly """
        url = reverse("my_orders")
        self.assertEqual(resolve(url).func, my_orders)

    def test_add_review_url_resolves(self):
        """ Test if the add review URL resolves correctly """
        url = reverse("add_review", args=[1])
        self.assertEqual(resolve(url).func, add_review)

    def test_merchant_dashboard_url_resolves(self):
        """ Test if the merchant dashboard URL resolves correctly """
        url = reverse("merchant_dashboard")
        self.assertEqual(resolve(url).func, merchant_dashboard)

    def test_manage_items_url_resolves(self):
        """ Test if the manage items URL resolves correctly """
        url = reverse("manage_items")
        self.assertEqual(resolve(url).func, manage_items)

    def test_add_category_url_resolves(self):
        """ Test if the add category URL resolves correctly """
        url = reverse("add_category")
        self.assertEqual(resolve(url).func, add_category)

    def test_get_categories_url_resolves(self):
        """ Test if the get categories URL resolves correctly """
        url = reverse("get_categories")
        self.assertEqual(resolve(url).func, get_categories)

    def test_edit_item_url_resolves(self):
        """ Test if the edit item URL resolves correctly """
        url = reverse("edit_item", args=[1])
        self.assertEqual(resolve(url).func, edit_item)

    def test_item_details_url_resolves(self):
        """ Test if the item details URL resolves correctly """
        url = reverse("item_details", args=[1])
        self.assertEqual(resolve(url).func, item_details)

    def test_toggle_item_availability_url_resolves(self):
        """ Test if the toggle item availability URL resolves correctly """
        url = reverse("toggle_item_availability", args=[1])
        self.assertEqual(resolve(url).func, toggle_item_availability)

    def test_update_item_url_resolves(self):
        """ Test if the update item URL resolves correctly """
        url = reverse("update_item", args=["1"])
        self.assertEqual(resolve(url).func, update_item)

    def test_delete_item_url_resolves(self):
        """ Test if the delete item URL resolves correctly """
        url = reverse("delete_item", args=[1])
        self.assertEqual(resolve(url).func, delete_item)

    def test_merchant_orders_url_resolves(self):
        """ Test if the merchant orders management URL resolves correctly """
        url = reverse("merchant_orders")
        self.assertEqual(resolve(url).func, merchant_orders)

    def test_update_order_status_url_resolves(self):
        """ Test if the update order status URL resolves correctly """
        url = reverse("update_order_status", args=[1])
        self.assertEqual(resolve(url).func, update_order_status)

    def test_get_reviews_url_resolves(self):
        """ Test if the get reviews URL resolves correctly """
        url = reverse("get_reviews")
        self.assertEqual(resolve(url).func, get_reviews)