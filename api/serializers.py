from rest_framework import serializers
from .models import User, Product, Order, Wishlist, CartItem, OrderItem
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# ---------------------------------------------------
# ✅ Register Serializer
# ---------------------------------------------------


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    full_name = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "full_name",
            "email",
            "phone",
            "password",
            "is_buyer",
            "is_artisan",
        )

    def validate(self, data):
        if data.get("is_buyer") and data.get("is_artisan"):
            raise serializers.ValidationError("User cannot be both buyer and artisan.")
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            full_name=validated_data["full_name"],
            email=validated_data["email"],
            phone=validated_data["phone"],
            password=validated_data["password"],
            is_buyer=validated_data.get("is_buyer", False),
            is_artisan=validated_data.get("is_artisan", False),
            is_admin=False,
        )
        return user


# ---------------------------------------------------
# ✅ JWT Token Serializer with Role Info
# ---------------------------------------------------


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["full_name"] = user.full_name
        token["username"] = user.username
        token["is_buyer"] = user.is_buyer
        token["is_artisan"] = user.is_artisan
        token["is_admin"] = user.is_admin
        return token


# ---------------------------------------------------
# ✅ Product Serializer ---------------------------------------------------
# ✅ Order Serializer (Buyer/Artisan View)
# ---------------------------------------------------

# ---------------------------------------------------
# ✅ Updated Order Serializer (With Nested Items)
# ---------------------------------------------------


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("artisan", "created_at", "updated_at")

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            return (
                request.build_absolute_uri(obj.image.url) if request else obj.image.url
            )
        return None

#Order item Serializer
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_name = serializers.CharField(source="buyer.full_name", read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "buyer_name",
            "shipping_address",
            "phone_number",
            "payment_method",
            "status",
            "delivery_status",
            "delivery_date",
            "created_at",
            "items",
            "total_amount",
        ]
        read_only_fields = (
            "buyer",
            "status",
            "created_at",
            "delivery_status",
            "delivery_date",
        )

    def get_total_amount(self, obj):
        return sum(item.price * item.quantity for item in obj.items.all())


# ---------------------------------------------------
# ✅ Wishlist Serializer
# ---------------------------------------------------


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), write_only=True, source="product"
    )

    class Meta:
        model = Wishlist
        fields = ["id", "product", "product_id", "added_at"]


# ---------------------------------------------------
# ✅ Admin View - Users
# ---------------------------------------------------


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "email",
            "phone",
            "is_buyer",
            "is_artisan",
            "is_admin",
            "is_active",
            "date_joined",
        ]


# ---------------------------------------------------
# ✅ Admin View - Products
# ---------------------------------------------------


class AdminProductSerializer(serializers.ModelSerializer):
    artisan_name = serializers.CharField(source="artisan.full_name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "description",
            "category",
            "price",
            "stock",
            "artisan_name",
            "image",
            "created_at",
        ]


# ---------------------------------------------------
# ✅ Admin View - Orders
# ---------------------------------------------------


# ---------------------------------------------------
# ✅ Admin View - Orders (with nested items)
# ---------------------------------------------------
class AdminOrderSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.full_name", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "buyer_name",
            "shipping_address",
            "phone_number",
            "payment_method",
            "status",
            "delivery_status",
            "delivery_date",
            "created_at",
            "items",
        ]


# ---------------------------------------------------
# ✅ Cart Item Serializer
# ---------------------------------------------------


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)  # full nested product
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), write_only=True, source="product"
    )

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "added_at"]
