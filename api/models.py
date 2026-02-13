from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# ---------------------------------------------------
# ✅ Custom User Model
# ---------------------------------------------------


class User(AbstractUser):
    is_buyer = models.BooleanField(default=False)
    is_artisan = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    security_question = models.CharField(max_length=255, blank=True, null=True)
    security_answer = models.CharField(max_length=255, blank=True, null=True)

    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)

    def __str__(self):
        return self.username


# ---------------------------------------------------
# ✅ Product Model (Artisan)
# ---------------------------------------------------


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Pottery", "Pottery"),
        ("Woodcraft", "Woodcraft"),
        ("Textiles", "Textiles"),
        ("Jewelry", "Jewelry"),
        ("Leatherwork", "Leatherwork"),
        ("Sculptures", "Sculptures"),
    ]

    artisan = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=100, choices=CATEGORY_CHOICES
    )  # Updated here
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ---------------------------------------------------
# ✅ Order Model (Buyer)
# ---------------------------------------------------

# models.py


class Order(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    shipping_address = models.TextField(default="Not provided")
    phone_number = models.CharField(max_length=15, default="0000000000")
    payment_method = models.CharField(
        max_length=20,
        choices=[("cod", "Cash on Delivery"), ("upi", "UPI"), ("cc", "Credit Card")],
        default="cod",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("denied", "Denied"),
        ],
        default="pending",
    )
    delivery_status = models.CharField(
        max_length=30,
        choices=[
            ("pending", "Pending"),
            ("shipped", "Shipped"),
            ("out_for_delivery", "Out for Delivery"),
            ("delivered", "Delivered"),
        ],
        default="pending",
    )
    delivery_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username}"

    def set_estimated_delivery_date(self, days=5):
        self.delivery_date = timezone.now().date() + timedelta(days=days)
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # Snapshot of price at purchase time

    def __str__(self):
        return f"{self.product.title} × {self.quantity}"


# ---------------------------------------------------
# ✅ Wishlist Model (Buyer)
# ---------------------------------------------------


class Wishlist(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("buyer", "product")

    def __str__(self):
        return f"{self.buyer.username} ♥ {self.product.title}"


# ---------------------------------------------------
# ✅ CartItem Model (Multi-product support)
# ---------------------------------------------------


class CartItem(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("buyer", "product")

    def __str__(self):
        return f"{self.buyer.username} → {self.product.title} x {self.quantity}"


class Address(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=100, default="Home")  # e.g., Home, Office
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=50, default="India")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.username} - {self.label}"
