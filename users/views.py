from django.contrib.auth import get_user_model
from rest_framework import serializers, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from gawa_core.audit import audit_logger, get_client_ip
from gawa_core.permissions import (
    ROLE_ADMIN,
    ROLE_PLATFORM_SUPERADMIN,
    ROLE_SCHOOL_ADMIN,
    RolePolicyPermission,
)
from gawa_core.tenancy import get_request_school, is_platform_superadmin
from .models import School, SchoolMembership, User
from .serializers import SchoolMembershipSerializer, SchoolSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)

    def get_queryset(self):
        user = self.request.user
        if is_platform_superadmin(user):
            school = get_request_school(self.request)
            if school is None:
                return User.objects.all()
            return User.objects.filter(school_memberships__school=school).distinct()

        school = get_request_school(self.request)
        if school is None:
            return User.objects.none()
        return User.objects.filter(school_memberships__school=school).distinct()

    def perform_create(self, serializer):
        actor = self.request.user
        target_role = serializer.validated_data.get("role", "STUDENT")

        if not is_platform_superadmin(actor) and target_role == ROLE_PLATFORM_SUPERADMIN:
            raise ValidationError("Seul le superutilisateur plateforme peut créer ce rôle.")

        school = serializer.validated_data.get("default_school") or get_request_school(self.request)
        if not is_platform_superadmin(actor) and school is None:
            raise ValidationError("school_id ou default_school est requis pour créer un utilisateur d'école.")

        user = serializer.save(default_school=school)
        if school:
            SchoolMembership.objects.get_or_create(
                school=school,
                user=user,
                defaults={"is_active": True},
            )

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        target_user = self.get_object()
        if target_user.role != ROLE_SCHOOL_ADMIN:
            raise ValidationError("Le reset est autorisé uniquement pour un SCHOOL_ADMIN.")

        new_password = request.data.get("new_password")
        if not isinstance(new_password, str) or len(new_password) < 8:
            raise ValidationError("Le nouveau mot de passe doit contenir au moins 8 caractères.")

        target_user.set_password(new_password)
        target_user.save(update_fields=["password"])

        audit_logger.info(
            "auth.password_reset actor=%s target=%s target_role=%s ip=%s",
            request.user.email,
            target_user.email,
            target_user.role,
            get_client_ip(request),
        )

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (ROLE_PLATFORM_SUPERADMIN,)
    write_roles = (ROLE_PLATFORM_SUPERADMIN,)


class SchoolMembershipViewSet(viewsets.ModelViewSet):
    queryset = SchoolMembership.objects.select_related("user", "school").all()
    serializer_class = SchoolMembershipSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)

    def get_queryset(self):
        user = self.request.user
        if is_platform_superadmin(user):
            school = get_request_school(self.request)
            if school is None:
                return SchoolMembership.objects.select_related("user", "school").all()
            return SchoolMembership.objects.select_related("user", "school").filter(school=school)

        school = get_request_school(self.request)
        if school is None:
            return SchoolMembership.objects.none()

        return SchoolMembership.objects.select_related("user", "school").filter(school=school)

    def _get_actor_school(self):
        if is_platform_superadmin(self.request.user):
            return None
        return get_request_school(self.request)

    def perform_create(self, serializer):
        actor_school = self._get_actor_school()
        target_school = serializer.validated_data.get("school")

        if actor_school is None and not is_platform_superadmin(self.request.user):
            raise ValidationError("Contexte ecole requis.")

        if actor_school and target_school and target_school.id != actor_school.id:
            raise ValidationError("Impossible de creer une affectation hors scope ecole.")

        serializer.save()

    def perform_update(self, serializer):
        actor_school = self._get_actor_school()
        instance = self.get_object()
        target_school = serializer.validated_data.get("school", instance.school)

        if actor_school is None and not is_platform_superadmin(self.request.user):
            raise ValidationError("Contexte ecole requis.")

        if actor_school and (instance.school_id != actor_school.id or target_school.id != actor_school.id):
            raise ValidationError("Impossible de modifier une affectation hors scope ecole.")

        serializer.save()


class EmailOrUsernameTokenSerializer(TokenObtainPairSerializer):
    username_field = get_user_model().USERNAME_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = getattr(user, "role", "")
        token["email"] = user.email
        token["first_name"] = user.first_name or ""
        token["last_name"] = user.last_name or ""
        token["username"] = user.username or ""
        token["default_school_id"] = str(user.default_school_id) if user.default_school_id else None
        token["school_ids"] = [str(sid) for sid in user.school_memberships.values_list("school_id", flat=True)]
        return token

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"] = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        raw_identifier = attrs.get(self.username_field) or attrs.get("username")
        password = attrs.get("password")

        if raw_identifier is None or password is None:
            request = self.context.get("request")
            if request is not None:
                audit_logger.warning(
                    "auth.login_failed reason=missing_credentials identifier=%s ip=%s",
                    raw_identifier,
                    get_client_ip(request),
                )
            raise ValidationError("Email/username et mot de passe requis.")

        attrs[self.username_field] = raw_identifier
        try:
            tokens = super().validate(attrs)
            request = self.context.get("request")
            if request is not None:
                audit_logger.info(
                    "auth.login_success user=%s role=%s ip=%s",
                    self.user.email,
                    getattr(self.user, "role", ""),
                    get_client_ip(request),
                )
            return tokens
        except Exception:
            request = self.context.get("request")
            if request is not None:
                audit_logger.warning(
                    "auth.login_failed reason=bad_credentials identifier=%s ip=%s",
                    raw_identifier,
                    get_client_ip(request),
                )
            raise


class EmailOrUsernameTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenSerializer
    permission_classes = [AllowAny]
