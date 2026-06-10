from rest_framework.permissions import BasePermission


ROLE_ADMIN = "ADMIN"
ROLE_SCHOOL_ADMIN = "SCHOOL_ADMIN"
ROLE_PLATFORM_SUPERADMIN = "PLATFORM_SUPERADMIN"
ROLE_TEACHER = "TEACHER"
ROLE_STUDENT = "STUDENT"
ROLE_PARENT = "PARENT"

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class RolePolicyPermission(BasePermission):
    """
    Apply per-view role policy via:
      - `read_roles`: roles allowed for safe methods
      - `write_roles`: roles allowed for mutating methods
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        role = getattr(user, "role", None)
        read_roles = set(getattr(view, "read_roles", ()))
        write_roles = set(getattr(view, "write_roles", ()))

        if request.method in SAFE_METHODS:
            return role in (read_roles | write_roles)
        return role in write_roles
