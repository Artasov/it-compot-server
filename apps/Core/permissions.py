from rest_framework import permissions


class IsStaff(permissions.BasePermission):
    """
    Permission to only allow access to staff members.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated and is a staff member
        return request.user and request.user.is_authenticated and request.user.is_staff
