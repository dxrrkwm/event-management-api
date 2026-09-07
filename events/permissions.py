from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOrganizerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.organizer_id == request.user.id
