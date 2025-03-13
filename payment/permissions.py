from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS and (
            request.user == obj.borrowing.user or request.user.is_staff
        )
