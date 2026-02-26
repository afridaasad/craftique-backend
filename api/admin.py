from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Product


class UserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "full_name",
        "phone",
        "is_buyer",
        "is_artisan",
        "is_admin",
    )
    list_filter = ("is_buyer", "is_artisan", "is_admin")
    search_fields = ("username", "email", "full_name")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("username", "full_name", "email", "phone", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_buyer",
                    "is_artisan",
                    "is_admin",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        ("Groups & Permissions", {"fields": ("groups", "user_permissions")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "full_name",
                    "email",
                    "phone",
                    "password1",
                    "password2",
                    "is_buyer",
                    "is_artisan",
                ),
            },
        ),
    )


admin.site.register(User, UserAdmin)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "artisan",
        "price",
        "stock",
        "category",
        "created_at",
    )
    list_filter = ("category", "created_at")
    search_fields = ("title", "description", "category", "artisan__username")
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "artisan":
            from .models import User
            kwargs["queryset"] = User.objects.filter(
                is_artisan=True
            ) | User.objects.filter(is_superuser=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "get_products", "buyer", "status", "created_at")
    list_filter = ("status", "created_at")

    def get_products(self, obj):
        return ", ".join([item.product.title for item in obj.items.all()])

    get_products.short_description = "Products"
