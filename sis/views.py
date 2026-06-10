from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db.models import Q
from rest_framework import status, viewsets, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from gawa_core.audit import audit_logger, get_client_ip
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
from pcs.models import Course
from .models import Attendance, Classroom, LiaisonNote, Student, TimetableSlot
from .serializers import (
    AttendanceSerializer,
    ClassroomSerializer,
    LiaisonNoteSerializer,
    StudentSerializer,
    TimetableSlotSerializer,
)


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_STUDENT,
        ROLE_PARENT,
    )
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)

        if role in {ROLE_PLATFORM_SUPERADMIN}:
            if school:
                return Student.objects.filter(school=school)
            return Student.objects.all()
        if role in {ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER}:
            if school is None:
                return Student.objects.none()
            return Student.objects.filter(school=school)
        if role == ROLE_STUDENT:
            qs = Student.objects.filter(user=user)
            return qs.filter(school=school) if school else qs
        if role == ROLE_PARENT:
            qs = Student.objects.filter(parent_user=user)
            return qs.filter(school=school) if school else qs
        return Student.objects.none()

    def perform_create(self, serializer):
        school = get_request_school(self.request) or serializer.validated_data.get("school")
        serializer.save(school=school)


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER)
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)

    def get_queryset(self):
        school = get_request_school(self.request)
        if is_platform_superadmin(self.request.user):
            if school:
                return Classroom.objects.filter(school=school)
            return Classroom.objects.all()
        if school is None:
            return Classroom.objects.none()
        return Classroom.objects.filter(school=school)

    def perform_create(self, serializer):
        school = get_request_school(self.request) or serializer.validated_data.get("school")
        serializer.save(school=school)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
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

        if role in {ROLE_PLATFORM_SUPERADMIN}:
            qs = Attendance.objects.all()
            return qs.filter(student__school=school) if school else qs
        if role in {ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER}:
            if school is None:
                return Attendance.objects.none()
            return Attendance.objects.filter(student__school=school)
        if role == ROLE_STUDENT:
            qs = Attendance.objects.filter(student__user=user)
            return qs.filter(student__school=school) if school else qs
        if role == ROLE_PARENT:
            qs = Attendance.objects.filter(student__parent_user=user)
            return qs.filter(student__school=school) if school else qs
        return Attendance.objects.none()


class TimetableSlotViewSet(viewsets.ModelViewSet):
    queryset = TimetableSlot.objects.all()
    serializer_class = TimetableSlotSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_STUDENT,
        ROLE_PARENT,
    )
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)

        if role == ROLE_PLATFORM_SUPERADMIN:
            qs = TimetableSlot.objects.all()
            return qs.filter(school=school) if school else qs

        if school is None:
            return TimetableSlot.objects.none()

        qs = TimetableSlot.objects.filter(school=school)
        if role in {ROLE_SCHOOL_ADMIN, ROLE_ADMIN}:
            return qs
        if role == ROLE_TEACHER:
            return qs.filter(Q(teacher=user) | Q(teacher__isnull=True))
        if role == ROLE_STUDENT:
            return qs.filter(classroom__students__user=user).distinct()
        if role == ROLE_PARENT:
            return qs.filter(classroom__students__parent_user=user).distinct()
        return TimetableSlot.objects.none()

    def perform_create(self, serializer):
        school = get_request_school(self.request)
        if school is None:
            school = serializer.validated_data.get("school")
        serializer.save(school=school)


class SyncAttendanceView(views.APIView):
    """
    Endpoint: POST /api/v1/attendance/sync
    Gère la synchronisation offline-first des appels effectués par les professeurs.
    """
    permission_classes = [IsAuthenticated]

    def _can_sync(self, request):
        return getattr(request.user, "role", None) in {
            ROLE_PLATFORM_SUPERADMIN,
            ROLE_SCHOOL_ADMIN,
            ROLE_ADMIN,
            ROLE_TEACHER,
        }

    def post(self, request):
        if not self._can_sync(request):
            return Response({"detail": "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)

        records = request.data.get("records", [])
        saved_ids = []
        errors = []

        for record in records:
            student_id = record.get("student_id")
            status_val = record.get("type")
            recorded_at = parse_datetime(record.get("recorded_at"))

            if not all([student_id, status_val, recorded_at]):
                errors.append({"record": record, "error": "Missing fields"})
                continue

            try:
                student = Student.objects.get(id=student_id)
                school = get_request_school(request)
                if school and student.school_id != school.id:
                    errors.append({"record": record, "error": "Student outside school scope"})
                    continue
                attendance, _ = Attendance.objects.update_or_create(
                    student=student,
                    date=recorded_at,
                    defaults={"status": status_val, "is_synced": True},
                )
                saved_ids.append(str(attendance.id))
            except Student.DoesNotExist:
                errors.append({"record": record, "error": "Student not found"})

        audit_logger.info(
            "sis.attendance_sync user=%s role=%s records=%s saved=%s errors=%s ip=%s",
            request.user.email,
            getattr(request.user, "role", ""),
            len(records),
            len(saved_ids),
            len(errors),
            get_client_ip(request),
        )
        return Response({"synced_ids": saved_ids, "errors": errors}, status=status.HTTP_200_OK)


class WatermelonSyncView(views.APIView):
    """
    Unified Sync endpoint for WatermelonDB (Mobile)
    Handles pull/push for students, attendance and courses.
    Contract intentionally mirrors local mobile schema columns.
    """
    permission_classes = [IsAuthenticated]

    def _can_sync(self, request):
        return getattr(request.user, "role", None) in {
            ROLE_PLATFORM_SUPERADMIN,
            ROLE_SCHOOL_ADMIN,
            ROLE_ADMIN,
            ROLE_TEACHER,
        }

    def _to_millis(self, dt):
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)

    def _student_payload(self, student):
        classroom = student.classrooms.order_by("-updated_at").first()
        return {
            "id": str(student.id),
            "matricule": student.matricule,
            "first_name": student.user.first_name or "",
            "last_name": student.user.last_name or "",
            "classroom_id": str(classroom.id) if classroom else "",
            "last_status": "PRESENT",
            "updated_at": self._to_millis(student.updated_at),
        }

    def _attendance_payload(self, attendance):
        return {
            "id": str(attendance.id),
            "student_id": str(attendance.student_id),
            "status": attendance.status,
            "date": attendance.date.isoformat(),
            "is_synced": attendance.is_synced,
            "created_at": self._to_millis(attendance.created_at),
            "updated_at": self._to_millis(attendance.updated_at),
        }

    def _course_payload(self, course):
        teacher_name = course.teacher.get_full_name().strip() or course.teacher.username
        return {
            "id": str(course.id),
            "title": course.title,
            "description": course.description or "",
            "teacher_name": teacher_name or "",
            "updated_at": self._to_millis(course.updated_at),
        }

    def _is_after(self, dt, pivot):
        if dt is None:
            return False
        return dt > pivot

    def get(self, request):
        if not self._can_sync(request):
            return Response({"detail": "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)

        raw_last_pulled_at = request.query_params.get("last_pulled_at", 0)
        try:
            last_pulled_at = int(raw_last_pulled_at)
            last_pulled_dt = timezone.datetime.fromtimestamp(
                last_pulled_at / 1000, tz=timezone.utc
            )
        except (TypeError, ValueError):
            last_pulled_dt = timezone.datetime.fromtimestamp(0, tz=timezone.utc)

        school = get_request_school(request)
        students = Student.objects.filter(updated_at__gt=last_pulled_dt).select_related("user")
        attendance = Attendance.objects.filter(updated_at__gt=last_pulled_dt)
        courses = Course.objects.filter(updated_at__gt=last_pulled_dt).select_related("teacher")

        if school:
            students = students.filter(school=school)
            attendance = attendance.filter(student__school=school)
            courses = courses.filter(
                Q(classroom__school=school)
                | Q(classroom__isnull=True, teacher__default_school=school)
            )

        student_created, student_updated = [], []
        attendance_created, attendance_updated = [], []
        course_created, course_updated = [], []

        for student in students:
            payload = self._student_payload(student)
            if self._is_after(student.created_at, last_pulled_dt):
                student_created.append(payload)
            else:
                student_updated.append(payload)

        for att in attendance:
            payload = self._attendance_payload(att)
            if self._is_after(att.created_at, last_pulled_dt):
                attendance_created.append(payload)
            else:
                attendance_updated.append(payload)

        for course in courses:
            payload = self._course_payload(course)
            if self._is_after(course.created_at, last_pulled_dt):
                course_created.append(payload)
            else:
                course_updated.append(payload)

        response = Response(
            {
                "changes": {
                    "students": {
                        "created": student_created,
                        "updated": student_updated,
                        "deleted": [],
                    },
                    "attendance": {
                        "created": attendance_created,
                        "updated": attendance_updated,
                        "deleted": [],
                    },
                    "courses": {
                        "created": course_created,
                        "updated": course_updated,
                        "deleted": [],
                    },
                },
                "timestamp": int(timezone.now().timestamp() * 1000),
            }
        )
        audit_logger.info(
            "sis.watermelon_pull user=%s role=%s students=%s attendance=%s courses=%s ip=%s",
            request.user.email,
            getattr(request.user, "role", ""),
            len(student_created) + len(student_updated),
            len(attendance_created) + len(attendance_updated),
            len(course_created) + len(course_updated),
            get_client_ip(request),
        )
        return response

    def post(self, request):
        if not self._can_sync(request):
            return Response({"detail": "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)

        changes = request.data.get("changes", {})
        attendance_changes = changes.get("attendance", {})
        incoming_rows = []
        incoming_rows.extend(attendance_changes.get("created", []))
        incoming_rows.extend(attendance_changes.get("updated", []))

        synced_ids = []
        errors = []

        for row in incoming_rows:
            student_id = row.get("student_id")
            status_val = row.get("status")
            date_raw = row.get("date")

            if status_val not in {"ABSENT", "LATE"}:
                # PRESENT is represented by the absence of attendance record.
                continue

            if not all([student_id, status_val, date_raw]):
                errors.append({"record": row, "error": "Missing required fields"})
                continue

            dt = parse_datetime(date_raw)
            if dt is None:
                errors.append({"record": row, "error": "Invalid datetime format"})
                continue
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())

            try:
                student = Student.objects.get(id=student_id)
                school = get_request_school(request)
                if school and student.school_id != school.id:
                    errors.append({"record": row, "error": "Student outside school scope"})
                    continue
            except Student.DoesNotExist:
                errors.append({"record": row, "error": "Student not found"})
                continue

            try:
                # Watermelon local ids are not UUIDs; upsert on business key.
                attendance_obj, _ = Attendance.objects.update_or_create(
                    student=student,
                    date=dt,
                    defaults={"status": status_val, "is_synced": True},
                )
                synced_ids.append(str(attendance_obj.id))
            except Exception as exc:
                errors.append({"record": row, "error": str(exc)})

        audit_logger.info(
            "sis.watermelon_push user=%s role=%s rows=%s synced=%s errors=%s ip=%s",
            request.user.email,
            getattr(request.user, "role", ""),
            len(incoming_rows),
            len(synced_ids),
            len(errors),
            get_client_ip(request),
        )
        return Response({"status": "ok", "synced_ids": synced_ids, "errors": errors}, status=200)


class LiaisonNoteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint: GET /api/v1/students/{id}/carnet
    """

    serializer_class = LiaisonNoteSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_PARENT,
        ROLE_STUDENT,
    )
    write_roles = ()

    def get_queryset(self):
        student_id = self.kwargs.get("student_pk")
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)

        if not student_id:
            return LiaisonNote.objects.none()

        qs = LiaisonNote.objects.filter(student_id=student_id).order_by("-created_at")
        if school:
            qs = qs.filter(student__school=school)

        if role in {ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER}:
            return qs
        if role == ROLE_STUDENT:
            return qs.filter(student__user=user)
        if role == ROLE_PARENT:
            return qs.filter(student__parent_user=user)
        return LiaisonNote.objects.none()
