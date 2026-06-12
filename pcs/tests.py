from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from pcs.models import Chapter, Course, Resource
from sis.models import Classroom, Student
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


class ResourceClassScopingTests(APITestCase):
    """Cloisonnement par classe : un élève ne voit que les ressources de SA classe."""

    def setUp(self):
        user_model = get_user_model()
        self.school = School.objects.create(code="SCH-CLS", name="School Class")
        self.teacher = user_model.objects.create_user(
            username="t_cls", email="t_cls@gawa.local", password="StrongPass123!",
            role="TEACHER", default_school=self.school,
        )

        self.room_6 = Classroom.objects.create(school=self.school, name="6ème A", academic_year="2025")
        self.room_4 = Classroom.objects.create(school=self.school, name="4ème A", academic_year="2025")

        def make_student(suffix, room):
            u = user_model.objects.create_user(
                username=f"st_{suffix}", email=f"st_{suffix}@gawa.local",
                password="StrongPass123!", role="STUDENT", default_school=self.school,
            )
            s = Student.objects.create(user=u, school=self.school, matricule=f"CLS-{suffix}")
            room.students.add(s)
            return u

        self.student_6 = make_student("6", self.room_6)
        self.student_4 = make_student("4", self.room_4)

        # Cours de 6ème + ressource élève publiée.
        self.course_6 = Course.objects.create(teacher=self.teacher, classroom=self.room_6, title="Maths 6ème")
        self.chapter_6 = Chapter.objects.create(course=self.course_6, title="Ch1", order=1, status="UNLOCKED")
        self.res_6 = Resource.objects.create(
            chapter=self.chapter_6, title="Annale 6ème", type="PDF", status="UNLOCKED",
            document_class="PEDAGOGICAL_RESTRICTED", target_audiences=["STUDENT"],
            url="https://example.com/a6.pdf",
        )

    def test_student_does_not_see_other_class_resources(self):
        self.client.force_authenticate(user=self.student_4)
        res = self.client.get("/api/v1/pcs/resources/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        titles = [r["title"] for r in res.data]
        self.assertNotIn("Annale 6ème", titles)

    def test_student_sees_own_class_resources(self):
        self.client.force_authenticate(user=self.student_6)
        res = self.client.get("/api/v1/pcs/resources/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        titles = [r["title"] for r in res.data]
        self.assertIn("Annale 6ème", titles)

    def test_student_chapters_are_class_scoped(self):
        self.client.force_authenticate(user=self.student_4)
        res = self.client.get("/api/v1/pcs/chapters/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in res.data]
        self.assertNotIn(str(self.chapter_6.id), ids)

    def test_standalone_resource_requires_classroom(self):
        self.client.force_authenticate(user=self.teacher)
        payload = {
            "title": "Ressource libre", "type": "LINK", "status": "UNLOCKED",
            "target_audiences": ["STUDENT"], "url": "https://example.com/x",
        }
        res = self.client.post(
            "/api/v1/pcs/resources/", payload, format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
