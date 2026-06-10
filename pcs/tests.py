from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from pcs.models import Chapter, Course, Resource
from sis.models import Student
from users.models import School


class ResourceHubPolicyTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.school = School.objects.create(code="SCH-PCS", name="School PCS")

        self.teacher = user_model.objects.create_user(
            username="teacherpcs",
            email="teacherpcs@gawa.local",
            password="StrongPass123!",
            role="TEACHER",
            default_school=self.school,
        )
        self.student_user = user_model.objects.create_user(
            username="studentpcs",
            email="studentpcs@gawa.local",
            password="StrongPass123!",
            role="STUDENT",
            default_school=self.school,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            school=self.school,
            matricule="PCS-ST-001",
            parent_user=None,
        )

        self.course = Course.objects.create(
            teacher=self.teacher,
            title="Cours PCS",
            description="Cours test",
        )
        self.chapter = Chapter.objects.create(
            course=self.course,
            title="Chapitre PCS",
            order=1,
            status="UNLOCKED",
        )

    def test_cannot_create_official_archive_resource(self):
        self.client.force_authenticate(user=self.teacher)
        payload = {
            "chapter": str(self.chapter.id),
            "title": "Bulletin officiel",
            "type": "PDF",
            "url": "https://example.com/bulletin.pdf",
            "document_class": "OFFICIAL_ARCHIVE_VAULT",
            "target_audiences": ["PARENT"],
            "status": "LOCKED",
        }
        response = self.client.post("/api/v1/pcs/resources/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("document_class", response.data)

    def test_student_sees_only_unlocked_student_audience_resources(self):
        Resource.objects.create(
            chapter=self.chapter,
            title="Sujet bac 2024",
            type="PDF",
            status="UNLOCKED",
            document_class="AI_TRAINING_CORPUS",
            target_audiences=["STUDENT"],
            ai_eligible=True,
            url="https://example.com/sujet.pdf",
        )
        Resource.objects.create(
            chapter=self.chapter,
            title="Reglement parent",
            type="PDF",
            status="UNLOCKED",
            document_class="SCHOOL_COMMUNICATION",
            target_audiences=["PARENT"],
            ai_eligible=False,
            url="https://example.com/reglement.pdf",
        )

        self.client.force_authenticate(user=self.student_user)
        response = self.client.get("/api/v1/pcs/resources/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Sujet bac 2024")
