from rest_framework.permissions import BasePermission


class IsBuyer(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_buyer


class IsArtisan(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated and request.user.is_artisan
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin
