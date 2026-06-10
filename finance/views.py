from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from gawa_core.permissions import (
    ROLE_ADMIN,
    ROLE_PARENT,
    ROLE_PLATFORM_SUPERADMIN,
    ROLE_SCHOOL_ADMIN,
    ROLE_STUDENT,
    RolePolicyPermission,
)
from gawa_core.tenancy import get_request_school, is_platform_superadmin

from .models import BroadcastMessage, Invoice, Payment
from .serializers import BroadcastMessageSerializer, InvoiceSerializer, PaymentSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_PARENT, ROLE_STUDENT)
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        base_qs = Invoice.objects.select_related("student", "student__user", "student__parent_user", "student__school")

        if is_platform_superadmin(user):
            if school:
                return base_qs.filter(student__school=school)
            return base_qs

        if school is None:
            return Invoice.objects.none()

        school_qs = base_qs.filter(student__school=school)
        if role in {ROLE_SCHOOL_ADMIN, ROLE_ADMIN}:
            return school_qs
        if role == ROLE_STUDENT:
            return school_qs.filter(student__user=user)
        if role == ROLE_PARENT:
            return school_qs.filter(student__parent_user=user)
        return Invoice.objects.none()


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_PARENT, ROLE_STUDENT)
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        base_qs = Payment.objects.select_related(
            "invoice",
            "invoice__student",
            "invoice__student__user",
            "invoice__student__parent_user",
            "invoice__student__school",
        )

        if is_platform_superadmin(user):
            if school:
                return base_qs.filter(invoice__student__school=school)
            return base_qs

        if school is None:
            return Payment.objects.none()

        school_qs = base_qs.filter(invoice__student__school=school)
        if role in {ROLE_SCHOOL_ADMIN, ROLE_ADMIN}:
            return school_qs
        if role == ROLE_STUDENT:
            return school_qs.filter(invoice__student__user=user)
        if role == ROLE_PARENT:
            return school_qs.filter(invoice__student__parent_user=user)
        return Payment.objects.none()

    def perform_create(self, serializer):
        school = get_request_school(self.request)
        invoice = serializer.validated_data.get("invoice")
        if invoice is None:
            raise PermissionDenied("La facture est requise.")

        if school and invoice.student.school_id != school.id:
            raise PermissionDenied("Facture hors scope école.")

        serializer.save(recorded_by=self.request.user)


class BroadcastMessageViewSet(viewsets.ModelViewSet):
    queryset = BroadcastMessage.objects.all()
    serializer_class = BroadcastMessageSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_PARENT, ROLE_STUDENT)
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)

    def get_queryset(self):
        user = self.request.user
        school = get_request_school(self.request)
        base_qs = BroadcastMessage.objects.select_related("school", "sent_by")

        if is_platform_superadmin(user):
            if school:
                return base_qs.filter(school=school)
            return base_qs

        if school is None:
            return BroadcastMessage.objects.none()

        return base_qs.filter(school=school)

    def perform_create(self, serializer):
        school = get_request_school(self.request)
        if school is None and not is_platform_superadmin(self.request.user):
            raise PermissionDenied("Le contexte école est requis.")
        serializer.save(sent_by=self.request.user, school=school)
