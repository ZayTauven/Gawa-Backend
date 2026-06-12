from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from gawa_core.permissions import (
    ROLE_ADMIN,
    ROLE_PARENT,
    ROLE_PLATFORM_SUPERADMIN,
    ROLE_SCHOOL_ADMIN,
    ROLE_STUDENT,
    ROLE_TEACHER,
    RolePolicyPermission,
)
from gawa_core.tenancy import get_request_school, is_platform_superadmin

from .models import Chapter, Course, Resource
from .serializers import ChapterSerializer, CourseSerializer, ResourceSerializer


def _course_school_q(school):
    return Q(classroom__school=school) | Q(
        classroom__isnull=True,
        teacher__default_school=school,
    )


def _chapter_school_q(school):
    return Q(course__classroom__school=school) | Q(
        course__classroom__isnull=True,
        course__teacher__default_school=school,
    )


def _resource_school_q(school):
    return (
        Q(chapter__course__classroom__school=school)
        | Q(
            chapter__course__classroom__isnull=True,
            chapter__course__teacher__default_school=school,
        )
        # Ressource autonome (hors cours) : ancrée à l'école via sa classe cible.
        | Q(chapter__isnull=True, classroom__school=school)
    )


def _resource_ids_for_audience(queryset, audience: str):
    ids = []
    for resource in queryset:
        audiences = resource.target_audiences or []
        if audience in audiences:
            ids.append(resource.id)
    return ids


# --- Cloisonnement par classe (visibilité élève/parent) -------------------
# Règle : un contenu LIÉ à une classe n'est visible qu'aux membres de cette classe ;
# un contenu SANS classe (classroom NULL) est école entière (partage intentionnel).

def _course_class_visible_q(user):
    return Q(classroom__isnull=True) | Q(classroom__students__user=user)


def _chapter_class_visible_q(user):
    return Q(course__classroom__isnull=True) | Q(course__classroom__students__user=user)


def _resource_class_visible_q(user):
    # Ressource de chapitre → classe du cours ; ressource autonome → classe directe.
    chapter_path = Q(chapter__isnull=False) & (
        Q(chapter__course__classroom__isnull=True)
        | Q(chapter__course__classroom__students__user=user)
    )
    standalone_path = Q(chapter__isnull=True) & (
        Q(classroom__isnull=True) | Q(classroom__students__user=user)
    )
    return chapter_path | standalone_path


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_STUDENT,
        ROLE_PARENT,
    )
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        base_qs = Course.objects.all()

        if is_platform_superadmin(user):
            if school:
                return base_qs.filter(_course_school_q(school)).distinct()
            return base_qs

        if school is None:
            return Course.objects.none()

        school_qs = base_qs.filter(_course_school_q(school)).distinct()
        if role in {ROLE_SCHOOL_ADMIN, ROLE_ADMIN}:
            return school_qs
        if role == ROLE_TEACHER:
            return school_qs.filter(teacher=user)
        if role in {ROLE_STUDENT, ROLE_PARENT}:
            return school_qs.filter(_course_class_visible_q(user)).distinct()
        return school_qs

    def perform_create(self, serializer):
        user = self.request.user
        school = get_request_school(self.request)

        if not is_platform_superadmin(user) and school is None:
            raise PermissionDenied("Le contexte ecole est requis.")

        if getattr(user, "role", None) == ROLE_TEACHER:
            if school and user.default_school_id and user.default_school_id != school.id:
                raise PermissionDenied("Vous ne pouvez pas creer un cours hors de votre ecole.")
            serializer.save(teacher=user)
            return

        if (
            school
            and user.default_school_id
            and user.default_school_id != school.id
            and not is_platform_superadmin(user)
        ):
            raise PermissionDenied("Vous ne pouvez pas creer un cours hors de votre ecole.")
        serializer.save(teacher=user)


class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_STUDENT,
        ROLE_PARENT,
    )
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        base_qs = Chapter.objects.select_related("course", "course__teacher", "course__classroom")

        if is_platform_superadmin(user):
            if school:
                return base_qs.filter(_chapter_school_q(school)).distinct()
            return base_qs

        if school is None:
            return Chapter.objects.none()

        school_qs = base_qs.filter(_chapter_school_q(school)).distinct()
        if role in {ROLE_SCHOOL_ADMIN, ROLE_ADMIN}:
            return school_qs
        if role == ROLE_TEACHER:
            return school_qs.filter(course__teacher=user)
        if role in {ROLE_STUDENT, ROLE_PARENT}:
            return school_qs.filter(_chapter_class_visible_q(user)).distinct()
        return school_qs

    def perform_create(self, serializer):
        user = self.request.user
        school = get_request_school(self.request)
        course = serializer.validated_data.get("course")

        if course is None:
            raise PermissionDenied("Le cours est requis.")

        if school:
            in_scope = (
                (course.classroom_id and course.classroom and course.classroom.school_id == school.id)
                or (course.classroom_id is None and course.teacher.default_school_id == school.id)
            )
            if not in_scope:
                raise PermissionDenied("Cours hors scope ecole.")

        if getattr(user, "role", None) == ROLE_TEACHER and course.teacher_id != user.id:
            raise PermissionDenied("Vous ne pouvez pas creer un chapitre sur ce cours.")
        serializer.save()


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_STUDENT,
        ROLE_PARENT,
    )
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        base_qs = Resource.objects.select_related(
            "chapter",
            "chapter__course",
            "chapter__course__teacher",
            "chapter__course__classroom",
        )

        if is_platform_superadmin(user):
            if school:
                return base_qs.filter(_resource_school_q(school)).distinct()
            return base_qs

        if school is None:
            return Resource.objects.none()

        school_qs = base_qs.filter(_resource_school_q(school)).distinct()
        if role in {ROLE_SCHOOL_ADMIN, ROLE_ADMIN}:
            return school_qs
        if role == ROLE_TEACHER:
            # Ressources de SES cours + SES ressources autonomes (hors cours).
            return school_qs.filter(
                Q(chapter__course__teacher=user) | Q(chapter__isnull=True, author=user)
            ).distinct()
        if role == ROLE_STUDENT:
            visible = (
                school_qs.filter(status="UNLOCKED")
                .filter(_resource_class_visible_q(user))
                .distinct()
            )
            return visible.filter(id__in=_resource_ids_for_audience(visible, "STUDENT"))
        if role == ROLE_PARENT:
            visible = (
                school_qs.filter(status="UNLOCKED")
                .filter(_resource_class_visible_q(user))
                .distinct()
            )
            return visible.filter(id__in=_resource_ids_for_audience(visible, "PARENT"))
        return school_qs

    def perform_create(self, serializer):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        chapter = serializer.validated_data.get("chapter")
        classroom = serializer.validated_data.get("classroom")

        if not is_platform_superadmin(user) and school is None:
            raise PermissionDenied("Le contexte ecole est requis.")

        # --- Ressource rattachée à un cours (via chapitre) ---
        if chapter is not None:
            if school:
                course = chapter.course
                in_scope = (
                    (course.classroom_id and course.classroom and course.classroom.school_id == school.id)
                    or (course.classroom_id is None and course.teacher.default_school_id == school.id)
                )
                if not in_scope:
                    raise PermissionDenied("Chapitre hors scope ecole.")
            if role == ROLE_TEACHER and chapter.course.teacher_id != user.id:
                raise PermissionDenied("Vous ne pouvez pas creer une ressource sur ce chapitre.")
            serializer.save(author=user)
            return

        # --- Ressource autonome (hors cours) : doit cibler une classe de l'école ---
        if classroom is None:
            raise PermissionDenied(
                "Une ressource hors cours doit cibler une classe (champ classroom)."
            )
        if school and classroom.school_id != school.id:
            raise PermissionDenied("Classe cible hors scope ecole.")
        serializer.save(author=user)

    @action(detail=False, methods=["get"], url_path="published")
    def published(self, request):
        role = getattr(request.user, "role", None)
        queryset = self.filter_queryset(self.get_queryset()).filter(status="UNLOCKED")

        audience = request.query_params.get("audience", "").upper().strip()
        if role == ROLE_STUDENT:
            queryset = queryset.filter(id__in=_resource_ids_for_audience(queryset, "STUDENT"))
        elif role == ROLE_PARENT:
            queryset = queryset.filter(id__in=_resource_ids_for_audience(queryset, "PARENT"))
        elif role == ROLE_TEACHER:
            queryset = queryset.filter(id__in=_resource_ids_for_audience(queryset, "TEACHER"))
        elif audience in {"STUDENT", "PARENT", "TEACHER"}:
            queryset = queryset.filter(id__in=_resource_ids_for_audience(queryset, audience))

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
