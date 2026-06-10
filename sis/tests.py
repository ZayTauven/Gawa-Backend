from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from pcs.models import Course
from sis.models import Attendance, Classroom, Student, TimetableSlot
from users.models import School


class WatermelonSyncTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(code="SCH-SIS", name="School SIS")
        self.teacher = get_user_model().objects.create_user(
            username="teachsync",
            email="teachsync@example.com",
            password="StrongPass123!",
            role="TEACHER",
            default_school=self.school,
            first_name="Teach",
            last_name="Sync",
        )
        self.student_user = get_user_model().objects.create_user(
            username="studentsync",
            email="studentsync@example.com",
            password="StrongPass123!",
            role="STUDENT",
            default_school=self.school,
            first_name="Stud",
            last_name="Ent",
        )
        self.student = Student.objects.create(
            user=self.student_user,
            school=self.school,
            matricule="MAT-SYNC-001",
        )
        Course.objects.create(
            teacher=self.teacher,
            classroom=None,
            title="Maths 3eme",
            description="Cours test sync",
        )

    def test_watermelon_sync_denied_for_student_role(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get("/api/v1/sis/sync/watermelon/?last_pulled_at=0")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_watermelon_push_creates_attendance_for_teacher(self):
        self.client.force_authenticate(user=self.teacher)
        now_iso = timezone.now().isoformat()
        payload = {
            "changes": {
                "attendance": {
                    "created": [
                        {
                            "id": "local-temp-id-1",
                            "student_id": str(self.student.id),
                            "status": "ABSENT",
                            "date": now_iso,
                        }
                    ],
                    "updated": [],
                    "deleted": [],
                }
            },
            "lastPulledAt": 0,
        }

        response = self.client.post(
            "/api/v1/sis/sync/watermelon/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(Attendance.objects.filter(student=self.student).count(), 1)


class TimetableSlotAPITests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(code="SCH-TT", name="School Timetable")
        self.admin = get_user_model().objects.create_user(
            username="schooladmin",
            email="schooladmin@example.com",
            password="StrongPass123!",
            role="SCHOOL_ADMIN",
            default_school=self.school,
            first_name="School",
            last_name="Admin",
        )
        self.teacher = get_user_model().objects.create_user(
            username="teachslot",
            email="teachslot@example.com",
            password="StrongPass123!",
            role="TEACHER",
            default_school=self.school,
            first_name="Teach",
            last_name="Slot",
        )
        self.classroom = Classroom.objects.create(
            school=self.school,
            name="6e A",
            academic_year="2025-2026",
        )

    def test_school_admin_can_create_timetable_slot(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "classroom": str(self.classroom.id),
            "teacher": str(self.teacher.id),
            "day_of_week": 1,
            "start_time": "08:00:00",
            "end_time": "09:00:00",
            "subject": "Mathematiques",
            "room": "Salle 2",
            "notes": "Cours de base",
        }

        response = self.client.post("/api/v1/sis/timetable-slots/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TimetableSlot.objects.count(), 1)
        slot = TimetableSlot.objects.first()
        self.assertEqual(slot.school, self.school)
        self.assertEqual(slot.classroom, self.classroom)
        self.assertEqual(slot.teacher, self.teacher)

    def test_timetable_slot_rejects_invalid_time_range(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "classroom": str(self.classroom.id),
            "teacher": str(self.teacher.id),
            "day_of_week": 1,
            "start_time": "10:00:00",
            "end_time": "09:00:00",
            "subject": "Mathematiques",
        }

        response = self.client.post("/api/v1/sis/timetable-slots/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TimetableSlot.objects.count(), 0)
