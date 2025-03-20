from django.core.exceptions import ValidationError
from django.test import TestCase

"""1.1 UserProfile"""
from django.contrib.auth.models import User
from shop.models import UserProfile

class UserProfileTest(TestCase):
    def setUp(self):
        """Create a regular user and a merchant"""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.merchant = User.objects.create_user(username="merchant", password="testpassword")

    def test_create_user_profile(self):
        """Test creating a UserProfile for a regular user"""
        profile = UserProfile.objects.create(user=self.user, phone_number="1234567890")
        self.assertFalse(profile.is_merchant)
        self.assertIsNone(profile.store_slug)

    def test_create_merchant_profile(self):
        """Test the automatic generation of store_slug for a merchant user"""
        profile = UserProfile.objects.create(user=self.merchant, is_merchant=True, store_name="Test Store")
        self.assertTrue(profile.is_merchant)
        self.assertEqual(profile.store_slug, "test-store")  # store_slug should be automatically generated


"""1.2 Item"""
from shop.models import Item, Category

class ItemTest(TestCase):
    def setUp(self):
        """Create a merchant, category, and item"""
        self.user = User.objects.create_user(username="merchant", password="testpassword")
        self.merchant = UserProfile.objects.create(user=self.user, is_merchant=True, store_name="Test Store")
        self.category = Category.objects.create(merchant=self.merchant, name="Beverages")

    def test_create_item(self):
        """Test whether an item is created correctly"""
        item = Item.objects.create(
            merchant=self.merchant,
            name="Milk Tea",
            price=10.00,
            category=self.category
        )
        self.assertEqual(item.name, "Milk Tea")
        self.assertEqual(item.merchant.store_name, "Test Store")
        self.assertEqual(item.category.name, "Beverages")


"""1.3 Order and OrderItem"""
from shop.models import Order, OrderItem
from decimal import Decimal

class OrderTest(TestCase):
    def setUp(self):
        """Create a user, merchant, item, and order"""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.merchant = UserProfile.objects.create(user=self.user, is_merchant=True, store_name="Test Store")
        self.item = Item.objects.create(name="Green Tea", price=5.00, merchant=self.merchant)

        self.order = Order.objects.create(
            customer=self.user,
            merchant=self.merchant,
            total_price=0.00  # Initially 0
        )

    def test_order_number_generation(self):
        """Test whether the order number is correctly generated"""
        self.assertIsNotNone(self.order.order_number)
        self.assertEqual(len(self.order.order_number), 10)  # The order number should be a 10-character random string

    def test_add_item_to_order(self):
        """Test adding an item to an order"""
        order_item = OrderItem.objects.create(order=self.order, item=self.item, quantity=2)
        self.assertEqual(order_item.get_total_price(), 10.00)  # 2 * 5.00 = 10.00

    def test_order_total_price_update(self):
        """Test updating the total price of an order"""
        OrderItem.objects.create(order=self.order, item=self.item, quantity=3)
        self.order.update_total_price()
        self.assertEqual(self.order.total_price, Decimal("15.00"))  # 3 * 5.00 = 15.00



"""1.4 Review"""
from shop.models import Review

class ReviewTest(TestCase):
    def setUp(self):
        """Create a user, merchant, item, order, and review"""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.merchant = UserProfile.objects.create(user=self.user, is_merchant=True, store_name="Test Store")
        self.item = Item.objects.create(name="Green Tea", price=5.00, merchant=self.merchant)
        self.order = Order.objects.create(customer=self.user, merchant=self.merchant, total_price=10.00)

    def test_create_review_for_item(self):
        """Test creating a review for an item"""
        review = Review.objects.create(user=self.user, item=self.item, rating=5, comment="Great!")
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great!")

    def test_create_review_for_order(self):
        """Test creating a review for an order"""
        review = Review.objects.create(user=self.user, order=self.order, rating=4, comment="Fast delivery!")
        self.assertEqual(review.order, self.order)
        self.assertEqual(review.rating, 4)

    def test_review_validation(self):
        """Test the `clean()` method to ensure that both `item` and `order` cannot exist simultaneously"""
        with self.assertRaises(ValidationError):
            review = Review(user=self.user, item=self.item, order=self.order, rating=5, comment="Invalid review")
            review.clean()