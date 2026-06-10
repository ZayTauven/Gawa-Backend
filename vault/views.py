from rest_framework import viewsets

from gawa_core.audit import audit_logger, get_client_ip
from gawa_core.permissions import (
    ROLE_ADMIN,
    ROLE_PLATFORM_SUPERADMIN,
    ROLE_SCHOOL_ADMIN,
    RolePolicyPermission,
)
from gawa_core.tenancy import get_request_school, is_platform_superadmin

from .models import ArchiveAccessLog, SealedArchive
from .serializers import ArchiveAccessLogSerializer, SealedArchiveSerializer

ARCHIVE_DB_ALIAS = "archive_db"


class SealedArchiveViewSet(viewsets.ModelViewSet):
    queryset = SealedArchive.objects.using(ARCHIVE_DB_ALIAS).all()
    serializer_class = SealedArchiveSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)

    def get_queryset(self):
        school = get_request_school(self.request)
        user = self.request.user

        if is_platform_superadmin(user):
            if school:
                return SealedArchive.objects.using(ARCHIVE_DB_ALIAS).filter(school_code=school.code)
            return SealedArchive.objects.using(ARCHIVE_DB_ALIAS).all()

        if school is None:
            return SealedArchive.objects.using(ARCHIVE_DB_ALIAS).none()
        return SealedArchive.objects.using(ARCHIVE_DB_ALIAS).filter(school_code=school.code)

    def perform_create(self, serializer):
        school = get_request_school(self.request)
        school_code = school.code if school else ""
        archive = serializer.save(school_code=school_code)
        audit_logger.info(
            "vault.sealed_archive_created user=%s school=%s target=%s year=%s ip=%s",
            self.request.user.email,
            school_code,
            archive.student_matricule,
            archive.academic_year,
            get_client_ip(self.request),
        )


class ArchiveAccessLogViewSet(viewsets.ModelViewSet):
    queryset = ArchiveAccessLog.objects.all()
    serializer_class = ArchiveAccessLogSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)

    def get_queryset(self):
        school = get_request_school(self.request)
        user = self.request.user

        if is_platform_superadmin(user):
            if school:
                return ArchiveAccessLog.objects.filter(school_code=school.code)
            return ArchiveAccessLog.objects.all()

        if school is None:
            return ArchiveAccessLog.objects.none()
        return ArchiveAccessLog.objects.filter(school_code=school.code)

    def perform_create(self, serializer):
        school = get_request_school(self.request)
        school_code = school.code if school else ""
        entry = serializer.save(
            school_code=school_code,
            admin_email=self.request.user.email,
            ip_address=get_client_ip(self.request),
        )
        audit_logger.info(
            "vault.access_log school=%s action=%s admin=%s target=%s ip=%s",
            school_code,
            entry.action_type,
            entry.admin_email,
            entry.target_matricule,
            entry.ip_address,
        )
