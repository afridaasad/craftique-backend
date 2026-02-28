from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from .views import (
    # Auth
    RegisterView,
    CustomLoginView,
    check_username,
    check_email,
    verify_user_phone,
    set_new_password_and_security,
    get_security_question,
    reset_password_with_security_answer,
    # Dashboard Views
    BuyerDashboardView,
    ArtisanDashboardView,
    AdminDashboardView,
    # Products
    ProductListView,
    ProductDetailView,
    ArtisanCreateProductView,
    ArtisanProductListView,
    ArtisanProductDetailView,
    toggle_product_status,
    # Orders
    BuyerOrderHistoryView,
    ArtisanOrderListView,
    update_order_status,
    update_delivery_status,
    AdminOrderListView,
    AdminOrderDetailView,
    # Admin User/Product
    AdminUserListView,
    AdminUserDetailView,
    AdminProductListView,
    AdminProductDetailView,
    # Analytics
    artisan_dashboard_analytics,
    admin_dashboard_analytics,
    # Wishlist
    WishlistView,
    WishlistDeleteView,
    # Cart
    CartListCreateView,
    CartItemUpdateDeleteView,
    buy_now_order,
    # Profile
    update_profile,
    update_password,
    get_profile,
    # Address (Buyer only)
    add_address,
    get_addresses,
    delete_address,
)

urlpatterns = [
    # 🔐 AUTH & JWT
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/login/", CustomLoginView.as_view(), name="custom_login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("auth/check-username/", check_username),
    path("auth/check-email/", check_email),
    # 🔁 FORGOT PASSWORD
    path("verify-user-phone/", verify_user_phone),
    path("set-password/", set_new_password_and_security),
    path("get-security-question/", get_security_question),
    path("reset-password-security/", reset_password_with_security_answer),
    # 👤 PROFILE
    path("profile/", get_profile),
    path("profile/update/", update_profile),
    path("profile/update-password/", update_password),
    # 🏠 DASHBOARDS
    path("buyer/dashboard/", BuyerDashboardView.as_view()),
    path("artisan/dashboard/", ArtisanDashboardView.as_view()),
    path("admin/dashboard/", AdminDashboardView.as_view()),
    # 🛍️ PRODUCTS
    path("products/", ProductListView.as_view()),
    path("products/<int:pk>/", ProductDetailView.as_view()),
    path("artisan/products/add/", ArtisanCreateProductView.as_view()),
    path("artisan/products/", ArtisanProductListView.as_view()),
    path("artisan/products/<int:pk>/", ArtisanProductDetailView.as_view()),
    path("artisan/products/<int:pk>/toggle-status/", toggle_product_status),
    # 📦 ORDERS
    path("buyer/orders/", BuyerOrderHistoryView.as_view()),
    path("buyer/buy-now/", buy_now_order),
    path("artisan/orders/", ArtisanOrderListView.as_view()),
    path("artisan/orders/<int:pk>/update-status/", update_order_status),
    path("orders/<int:pk>/update-delivery/", update_delivery_status),
    # 🧾 ADMIN
    path("admin/users/", AdminUserListView.as_view()),
    path("admin/users/<int:pk>/", AdminUserDetailView.as_view()),
    path("admin/products/", AdminProductListView.as_view()),
    path("admin/products/<int:pk>/", AdminProductDetailView.as_view()),
    path("admin/orders/", AdminOrderListView.as_view()),
    path("admin/orders/<int:pk>/", AdminOrderDetailView.as_view()),
    # 📊 ANALYTICS
    path("artisan/dashboard/analytics/", artisan_dashboard_analytics),
    path("admin/analytics/", admin_dashboard_analytics),
    # ❤️ WISHLIST
    path("buyer/wishlist/", WishlistView.as_view()),
    path("buyer/wishlist/<int:product_id>/", WishlistDeleteView.as_view()),
    # 🛒 CART
    path("buyer/cart/", CartListCreateView.as_view()),
    path("buyer/cart/<int:pk>/", CartItemUpdateDeleteView.as_view()),
    # 🏡 ADDRESS (Buyer)
    path("buyer/addresses/", get_addresses),
    path("buyer/addresses/add/", add_address),
    path("buyer/addresses/<int:address_id>/delete/", delete_address),
]

from .views import initiate_cart_checkout, checkout_confirm, create_razorpay_order

urlpatterns += [
    path("buyer/cart/checkout-initiate/", initiate_cart_checkout),
    path("buyer/cart/checkout-confirm/", checkout_confirm),
    path("buyer/cart/create-razorpay-order/", create_razorpay_order),
]
