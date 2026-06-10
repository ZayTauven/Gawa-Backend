from __future__ import annotations

from typing import Optional

from gawa_core.permissions import ROLE_PLATFORM_SUPERADMIN


def is_platform_superadmin(user) -> bool:
    return getattr(user, "role", None) == ROLE_PLATFORM_SUPERADMIN


def get_request_school(request) -> Optional["School"]:
    """
    Resolve active school from:
    1) X-School-ID header
    2) school_id query param
    3) user.default_school fallback (non-platform users)
    """
    user = request.user
    school_id = (
        request.headers.get("X-School-ID")
        or request.query_params.get("school_id")
        or request.data.get("school_id")
    )

    # Lazy import to avoid circular imports at startup.
    from users.models import School

    if school_id:
        qs = School.objects.filter(id=school_id, is_active=True)
        if is_platform_superadmin(user):
            return qs.first()

        return qs.filter(memberships__user=user, memberships__is_active=True).first()

    if is_platform_superadmin(user):
        return None

    default_school = getattr(user, "default_school", None)
    if default_school and default_school.is_active:
        return default_school
    return None
