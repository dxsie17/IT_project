from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from shop.models import UserProfile, Item, Category, Order, OrderItem
from decimal import Decimal

class ViewTests(TestCase):
    def setUp(self):
        """ Set up the test environment, creating users, merchants, and test data """
        self.client = Client()

        # Create a regular user
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.user_profile = UserProfile.objects.create(user=self.user, is_merchant=False)

        # Create a merchant user
        self.merchant = User.objects.create_user(username="merchant", password="merchantpass")
        self.merchant_profile = UserProfile.objects.create(user=self.merchant, is_merchant=True, store_name="Merchant Store")

        # Create a product category
        self.category = Category.objects.create(name="Milk Tea", merchant=self.merchant_profile)

        # Create a product
        self.item = Item.objects.create(
            name="Bubble Milk Tea",
            price=Decimal("5.99"),
            merchant=self.merchant_profile,
            category=self.category,
            is_available=True
        )

    def test_user_login(self):
        """ Test user login """
        response = self.client.post(reverse("user_login"), {"username": "testuser", "password": "testpassword"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True, "redirect_url": "/select-store/"})

    def test_merchant_login(self):
        """ Test merchant login """
        response = self.client.post(reverse("user_login"), {"username": "merchant", "password": "merchantpass"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True, "redirect_url": "/merchant/"})

    def test_register_user(self):
        """ Test new user registration """
        response = self.client.post(reverse("register"), {
            "email": "newuser@example.com",
            "phone": "123456789",
            "password1": "testpass",
            "password2": "testpass",
            "is_merchant": False
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after registration

        # Verify that the user is successfully created
        self.assertTrue(User.objects.filter(username="newuser@example.com").exists())

    def test_add_to_basket(self):
        """ Test adding an item to the shopping cart """
        self.client.login(username="testuser", password="testpassword")

        response = self.client.post(reverse("add_to_basket", args=[self.item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True, "message": "Product added to cart"})

        # Verify session cart content
        session = self.client.session
        self.assertIn(str(self.item.id), session["basket"])

    def test_get_cart(self):
        """ Test retrieving cart content """
        self.client.login(username="testuser", password="testpassword")
        session = self.client.session
        session["basket"] = {
            str(self.item.id): {
                "name": self.item.name,
                "price": float(self.item.price),
                "quantity": 2,
                "merchant_id": self.merchant_profile.id
            }
        }
        session.save()

        response = self.client.get(reverse("get_cart"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            "items": [
                {"id": str(self.item.id), "name": self.item.name, "quantity": 2, "unit_price": float(self.item.price), "total_price": float(self.item.price) * 2}
            ],
            "total_price": float(self.item.price) * 2
        })

    def test_checkout(self):
        """ Test order checkout """
        self.client.login(username="testuser", password="testpassword")
        session = self.client.session
        session["basket"] = {
            str(self.item.id): {
                "name": self.item.name,
                "price": float(self.item.price),
                "quantity": 2,
                "merchant_id": self.merchant_profile.id
            }
        }
        session.save()

        response = self.client.post(reverse("checkout"))
        self.assertEqual(response.status_code, 200)

        # Ensure the order is created
        self.assertTrue(Order.objects.filter(customer=self.user).exists())

    def test_get_orders(self):
        """ Test retrieving the user's order list """
        order = Order.objects.create(customer=self.user, merchant=self.merchant_profile, status="Ongoing", total_price=Decimal("10.00"))
        OrderItem.objects.create(order=order, item=self.item, quantity=1)

        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("my_orders"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user/my_orders.html")

    def test_add_review(self):
        """ Test user adding a review """
        order = Order.objects.create(customer=self.user, merchant=self.merchant_profile, status="Finished", total_price=Decimal("10.00"))

        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(reverse("add_review", args=[order.id]), {"rating": "5", "comment": "Great!"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True, "message": "Review submitted successfully"})

    def test_merchant_dashboard(self):
        """ Test merchant dashboard """
        self.client.login(username="merchant", password="merchantpass")
        response = self.client.get(reverse("merchant_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "merchant/dashboard.html")

    def test_toggle_item_availability(self):
        """ Test merchant toggling item availability """
        self.client.login(username="merchant", password="merchantpass")
        response = self.client.post(reverse("toggle_item_availability", args=[self.item.id]))
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_available)  # Ensure the status is updated

    def test_update_order_status(self):
        """ Test merchant updating order status """
        order = Order.objects.create(customer=self.user, merchant=self.merchant_profile, status="Ongoing", total_price=Decimal("10.00"))
        OrderItem.objects.create(order=order, item=self.item, quantity=1)

        self.client.login(username="merchant", password="merchantpass")
        response = self.client.post(reverse("update_order_status", args=[order.id]), {"status": "Finished"})
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, "Finished")  # Ensure the order status is updated