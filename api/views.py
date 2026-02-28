# ---------------------------------------------------
# ✅ Imports
# ---------------------------------------------------
from . import models
from rest_framework import generics, filters, permissions, status, serializers
from collections import defaultdict
from django.db.models import Count, Sum, F
from decimal import Decimal
from django.utils.timezone import now
from calendar import month_name
from django.db import IntegrityError
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import OrderItem, Product
from datetime import datetime
import calendar

from .models import User, Product, Order, Wishlist, CartItem, Address, OrderItem
from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    ProductSerializer,
    OrderSerializer,
    WishlistSerializer,
    CartItemSerializer,
    UserAdminSerializer,
    AdminProductSerializer,
    AdminOrderSerializer,
    OrderItemSerializer,
)
from .permissions import IsBuyer, IsArtisan, IsAdmin

# ---------------------------------------------------
# ✅ Auth & Registration
# ---------------------------------------------------


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# ---------------------------------------------------
# ✅ Dashboards (Role Based)
# ---------------------------------------------------


class BuyerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsBuyer]

    def get(self, request):
        return Response({"message": "Welcome Buyer!"})


class ArtisanDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsArtisan]

    def get(self, request):
        return Response({"message": "Welcome Artisan!"})


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({"message": "Welcome Admin!"})


# ---------------------------------------------------
# ✅ Live Field Validation (Register Form)
# ---------------------------------------------------


@api_view(["GET"])
def check_username(request):
    username = request.GET.get("username")
    exists = User.objects.filter(username=username).exists()
    return Response({"exists": exists})


@api_view(["GET"])
def check_email(request):
    email = request.GET.get("email")
    exists = User.objects.filter(email=email).exists()
    return Response({"exists": exists})


# ---------------------------------------------------
# ✅ Password Reset via Phone and security question
# ---------------------------------------------------


@api_view(["POST"])
def verify_user_phone(request):
    username = request.data.get("username")
    phone = request.data.get("phone")

    try:
        user = User.objects.get(username=username)
        if user.phone != phone:
            return Response({"status": "invalid_phone"}, status=400)

        if user.security_question and user.security_answer:
            return Response({"status": "already_has_security_question"})
        else:
            return Response({"status": "verified"})  # means they can now set it
    except User.DoesNotExist:
        return Response({"status": "user_not_found"}, status=404)


from django.contrib.auth.hashers import make_password


@api_view(["POST"])
def set_new_password_and_security(request):
    username = request.data.get("username")
    new_password = request.data.get("new_password")
    security_question = request.data.get("security_question")
    security_answer = request.data.get("security_answer")

    try:
        user = User.objects.get(username=username)
        user.password = make_password(new_password)
        user.security_question = security_question
        user.security_answer = security_answer  # You can hash this if needed
        user.save()
        return Response({"status": "password_updated"})
    except User.DoesNotExist:
        return Response({"status": "user_not_found"}, status=404)


@api_view(["POST"])
def get_security_question(request):
    username = request.data.get("username")
    try:
        user = User.objects.get(username=username)
        if user.security_question:
            return Response({"question": user.security_question})
        else:
            return Response({"error": "No security question set."}, status=400)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=404)


@api_view(["POST"])
def reset_password_with_security_answer(request):
    username = request.data.get("username")
    security_answer = request.data.get("security_answer")
    new_password = request.data.get("new_password")

    try:
        user = User.objects.get(username=username)
        if (
            user.security_answer
            and user.security_answer.strip().lower() == security_answer.strip().lower()
        ):
            user.password = make_password(new_password)
            user.save()
            return Response({"status": "password_reset_successful"})
        else:
            return Response({"error": "Incorrect security answer"}, status=403)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


# ---------------------------------------------------
# 🧑‍🎨 Artisan – Product Management
# ---------------------------------------------------


class ArtisanCreateProductView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsArtisan]

    def perform_create(self, serializer):
        serializer.save(artisan=self.request.user)


class ArtisanProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsArtisan]

    def get_queryset(self):
        return Product.objects.filter(artisan=self.request.user).order_by("-created_at")


class IsOwnerArtisan(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and obj.artisan == request.user
            and request.user.is_artisan
        )


class ArtisanProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsOwnerArtisan]
    queryset = Product.objects.all()


# ---------------------------------------------------
# 📦 Artisan – Order Management
# ---------------------------------------------------


class ArtisanOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsArtisan]

    def get_queryset(self):
        return (
            Order.objects.filter(items__product__artisan=self.request.user)
            .distinct()
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        return {"request": self.request}


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsArtisan])
def update_order_status(request, pk):
    try:
        order = Order.objects.prefetch_related("items__product").get(pk=pk)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    # ✅ Check that all items belong to this artisan
    if not order.items.filter(product__artisan=request.user).exists():
        return Response(
            {"error": "You do not have permission to modify this order."}, status=403
        )

    new_status = request.data.get("status")
    if new_status not in ["approved", "denied"]:
        return Response({"error": "Invalid status"}, status=400)

    order.status = new_status
    order.save()
    return Response({"success": True, "status": order.status})


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, F
from collections import defaultdict
from decimal import Decimal
from .models import OrderItem, Product


# ---------------------------------------------------
# 🛍️ Buyer Feed, Wishlist & Orders
# ---------------------------------------------------


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category"]
    search_fields = ["title", "description", "category"]
    ordering_fields = ["price", "created_at"]


class WishlistView(generics.ListCreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated, IsBuyer]

    def get_queryset(self):
        return Wishlist.objects.filter(buyer=self.request.user).order_by("-added_at")

    def perform_create(self, serializer):
        try:
            serializer.save(buyer=self.request.user)
        except IntegrityError:
            raise serializers.ValidationError(
                "This product is already in your wishlist."
            )


class WishlistDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsBuyer]
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(buyer=self.request.user)

    def get_object(self):
        product_id = self.kwargs["product_id"]
        return self.get_queryset().get(product__id=product_id)


class BuyerOrderHistoryView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsBuyer]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).order_by("-created_at")

    def get_serializer_context(self):
        return {"request": self.request}


# ---------------------------------------------------
# ✅ Buy Now – Direct Order
# ---------------------------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsBuyer])
def buy_now_order(request):
    user = request.user
    product_id = request.data.get("product_id")
    quantity = int(request.data.get("quantity", 1))

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)

    order = Order.objects.create(
        buyer=user,
        shipping_address=request.data.get("shipping_address", "Not provided"),
        phone_number=request.data.get("phone_number", "0000000000"),
        payment_method=request.data.get("payment_method", "cod"),
        status="pending",
        delivery_status="pending",
        delivery_date=timezone.now().date() + timedelta(days=5),
    )

    OrderItem.objects.create(
        order=order, product=product, quantity=quantity, price=product.price
    )

    return Response(
        {"success": True, "message": "Order placed via Buy Now", "order_id": order.id},
        status=201,
    )


# ---------------------------------------------------
# ✅ Cart & OTP Checkout (Multi-Item)
# ---------------------------------------------------


class CartListCreateView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsBuyer]

    def get_queryset(self):
        return CartItem.objects.filter(buyer=self.request.user).order_by("-added_at")

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)


from rest_framework.response import Response
from rest_framework import status


class CartItemUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsBuyer]

    def get_queryset(self):
        return CartItem.objects.filter(buyer=self.request.user)

    def update(self, request, *args, **kwargs):
        # Override to allow partial updates (e.g., just quantity)
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


# ✅ Restore this in views.py





# ✅ Restore this in views.py


class AdminOrderListView(generics.ListAPIView):
    serializer_class = AdminOrderSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Order.objects.prefetch_related("items__product", "buyer").order_by(
            "-created_at"
        )


class AdminOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminOrderSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = Order.objects.all()


from rest_framework import generics
from .permissions import IsAdmin
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserAdminSerializer


class AdminUserListView(generics.ListAPIView):
    serializer_class = UserAdminSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return User.objects.all().order_by("-date_joined")


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserAdminSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = User.objects.all()


from .models import Product
from .serializers import AdminProductSerializer


class AdminProductListView(generics.ListAPIView):
    serializer_class = AdminProductSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Product.objects.all().order_by("-created_at")


class AdminProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminProductSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = Product.objects.all()


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, F, FloatField


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_dashboard_analytics(request):
    total_users = User.objects.count()
    total_buyers = User.objects.filter(is_buyer=True).count()
    total_artisans = User.objects.filter(is_artisan=True).count()

    total_products = Product.objects.count()
    total_orders = Order.objects.count()

    approved_orders_count = Order.objects.filter(status="approved").count()
    pending_orders_count = Order.objects.filter(status="pending").count()
    denied_orders_count = Order.objects.filter(status="denied").count()

    # Efficient revenue calculation
    revenue_aggregate = OrderItem.objects.filter(order__status="approved").aggregate(
        total=Sum(F("price") * F("quantity"), output_field=FloatField())
    )
    revenue_estimate = revenue_aggregate["total"] or 0.0

    return Response(
        {
            "user_stats": {
                "total": total_users,
                "buyers": total_buyers,
                "artisans": total_artisans,
            },
            "product_stats": {"total_products": total_products},
            "order_stats": {
                "total_orders": total_orders,
                "status_breakdown": {
                    "approved": approved_orders_count,
                    "pending": pending_orders_count,
                    "denied": denied_orders_count,
                },
            },
            "estimated_revenue": round(revenue_estimate, 2),
        }
    )


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .models import User
from .serializers import RegisterSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request):
    user = request.user
    data = {
        "username": user.username,
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "profile_picture": (
            request.build_absolute_uri(user.profile.profile_picture.url)
            if hasattr(user, "profile") and user.profile.profile_picture
            else None
        ),
    }
    return Response(data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    full_name = request.data.get("full_name")
    phone = request.data.get("phone")
    profile_picture = request.FILES.get("profile_picture")

    user.full_name = full_name
    user.phone = phone

    if profile_picture:
        user.profile_picture = profile_picture

    user.save()
    return Response({"success": True, "message": "Profile updated."})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_password(request):
    user = request.user
    new_password = request.data.get("new_password")

    if not new_password or len(new_password) < 6:
        return Response(
            {"error": "Password must be at least 6 characters."}, status=400
        )

    user.set_password(new_password)
    user.save()

    return Response({"success": True, "message": "Password updated successfully."})


# Buyer-only: manage addresses
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsBuyer])
def add_address(request):
    buyer = request.user
    data = request.data

    required_fields = ["address_line", "city", "postal_code"]
    for field in required_fields:
        if not data.get(field):
            return Response(
                {"error": f"Missing required field: {field}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        address = Address.objects.create(
            buyer=buyer,
            label=data.get("label", "Home"),
            address_line=data["address_line"],
            city=data["city"],
            postal_code=data["postal_code"],
            country=data.get("country", "India"),
            is_default=data.get("is_default", False),
        )
        return Response({"success": True, "id": address.id})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsBuyer])
def get_addresses(request):
    buyer = request.user
    addresses = buyer.addresses.all().values()
    return Response(list(addresses))


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsBuyer])
def delete_address(request, address_id):
    try:
        address = Address.objects.get(id=address_id, buyer=request.user)
        address.delete()
        return Response({"success": True})
    except Address.DoesNotExist:
        return Response({"error": "Address not found"}, status=404)


import random
from django.core.cache import cache


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsBuyer])
def initiate_cart_checkout(request):
    buyer = request.user
    cart_items = CartItem.objects.filter(buyer=buyer)

    if not cart_items.exists():
        return Response({"error": "Your cart is empty."}, status=400)

    otp = random.randint(100000, 999999)
    cache.set(f"cart_checkout_otp_{buyer.id}", otp, timeout=300)  # 5 minutes

    return Response(
        {
            "success": True,
            "message": "OTP generated for checkout",
            "otp": otp,  # for now, show in response
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsBuyer])
def checkout_confirm(request):
    buyer = request.user
    entered_otp = request.data.get("otp")
    shipping_address = request.data.get("shipping_address", "Not provided")
    phone_number = request.data.get("phone_number", "0000000000")
    payment_method = request.data.get("payment_method", "cod")

    cached_otp = cache.get(f"cart_checkout_otp_{buyer.id}")

    if not cached_otp:
        return Response({"error": "OTP expired or not found."}, status=400)

    if str(entered_otp) != str(cached_otp):
        return Response({"error": "Invalid OTP."}, status=400)

    cart_items = CartItem.objects.filter(buyer=buyer)
    if not cart_items.exists():
        return Response({"error": "Your cart is empty."}, status=400)

    order = Order.objects.create(
        buyer=buyer,
        shipping_address=shipping_address,
        phone_number=phone_number,
        payment_method=payment_method,
        status="pending",
        delivery_status="pending",
        delivery_date=timezone.now().date() + timedelta(days=5),
    )

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )

    cart_items.delete()
    cache.delete(f"cart_checkout_otp_{buyer.id}")

    return Response(
        {"success": True, "message": "Order placed successfully via OTP checkout."}
    )


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Product
from .permissions import IsArtisan


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsArtisan])
def toggle_product_status(request, pk):
    try:
        product = Product.objects.get(pk=pk, artisan=request.user)
        product.is_active = not product.is_active
        product.save()
        return Response({"success": True, "is_active": product.is_active})
    except Product.DoesNotExist:
        return Response({"error": "Product not found or unauthorized."}, status=404)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsArtisan | IsAdmin])
def update_delivery_status(request, pk):
    try:
        order = Order.objects.prefetch_related("items__product").get(pk=pk)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    if request.user.is_artisan:
        if not order.items.filter(product__artisan=request.user).exists():
            return Response({"error": "Unauthorized"}, status=403)

    new_status = request.data.get("delivery_status")
    valid_statuses = ["shipped", "out_for_delivery", "delivered"]

    if new_status not in valid_statuses:
        return Response({"error": "Invalid delivery status"}, status=400)

    order.delivery_status = new_status
    order.save()

    return Response({"success": True, "delivery_status": new_status})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def artisan_dashboard_analytics(request):
    artisan = request.user
    orders = OrderItem.objects.filter(product__artisan=artisan).select_related(
        "product", "order"
    )

    monthly_earnings = defaultdict(float)
    for item in orders:
        month = item.order.created_at.strftime("%b")
        monthly_earnings[month] += float(item.price) * item.quantity

    response_data = {
        "total_sales": round(
            sum(float(item.price) * item.quantity for item in orders), 2
        ),
        "total_orders": orders.values("order_id").distinct().count(),
        "total_products": Product.objects.filter(artisan=artisan).count(),
        "avg_order_value": round(
            sum(float(item.price) * item.quantity for item in orders)
            / max(orders.values("order_id").distinct().count(), 1),
            2,
        ),
        "monthly_earnings": dict(monthly_earnings),
        "category_distribution": dict(
            Product.objects.filter(artisan=artisan)
            .values_list("category")
            .annotate(count=Count("id"))
        ),
        "top_selling_products": list(
            orders.values(title=F("product__title"))
            .annotate(total_quantity=Sum("quantity"))
            .order_by("-total_quantity")[:5]
        ),
        "recent_sales": list(
            orders.order_by("-order__created_at").values(
                title=F("product__title"),
                amount=F("price"),
                date=F("order__created_at"),
            )[:5]
        ),
    }

    return Response(response_data)


import razorpay
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_razorpay_order(request):
    try:
        amount = request.data.get("amount")  # in rupees
        shipping_address = request.data.get("shipping_address", "")

        if not amount:
            return Response({"error": "Amount is required"}, status=400)

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        # Razorpay expects amount in paise
        razorpay_order = client.order.create(
            {
                "amount": int(float(amount) * 100),
                "currency": "INR",
                "payment_capture": 1,
            }
        )

        return Response(
            {
                "order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"],
                "key": settings.RAZORPAY_KEY_ID,
            }
        )

    except Exception as e:
        return Response({"error": str(e)}, status=500)
