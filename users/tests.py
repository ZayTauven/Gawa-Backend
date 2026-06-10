from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import School, SchoolMembership


class AuthTokenTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="teacher01",
            email="teacher01@example.com",
            password="StrongPass123!",
            role="TEACHER",
            first_name="Ada",
            last_name="Lovelace",
        )

    def test_token_obtain_with_email_returns_jwt(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"email": self.user.email, "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_obtain_with_bad_password_returns_401(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {"email": self.user.email, "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MultiSchoolScopingTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.school_a = School.objects.create(code="GWA-A", name="Gawa School A")
        self.school_b = School.objects.create(code="GWA-B", name="Gawa School B")

        self.platform = user_model.objects.create_user(
            username="platform",
            email="platform@gawa.local",
            password="StrongPass123!",
            role="PLATFORM_SUPERADMIN",
        )
        self.school_admin = user_model.objects.create_user(
            username="schooladmin",
            email="schooladmin@gawa.local",
            password="StrongPass123!",
            role="SCHOOL_ADMIN",
            default_school=self.school_a,
        )
        self.teacher_a = user_model.objects.create_user(
            username="teachera",
            email="teachera@gawa.local",
            password="StrongPass123!",
            role="TEACHER",
            default_school=self.school_a,
        )
        self.teacher_b = user_model.objects.create_user(
            username="teacherb",
            email="teacherb@gawa.local",
            password="StrongPass123!",
            role="TEACHER",
            default_school=self.school_b,
        )

        SchoolMembership.objects.create(user=self.school_admin, school=self.school_a)
        SchoolMembership.objects.create(user=self.teacher_a, school=self.school_a)
        SchoolMembership.objects.create(user=self.teacher_b, school=self.school_b)

    def test_school_admin_sees_only_its_school_users(self):
        self.client.force_authenticate(user=self.school_admin)
        response = self.client.get("/api/v1/users/users/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = {row["email"] for row in response.data}
        self.assertIn("schooladmin@gawa.local", emails)
        self.assertIn("teachera@gawa.local", emails)
        self.assertNotIn("teacherb@gawa.local", emails)

    def test_platform_can_list_schools(self):
        self.client.force_authenticate(user=self.platform)
        response = self.client.get("/api/v1/users/schools/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_platform_can_reset_school_admin_password(self):
        self.client.force_authenticate(user=self.platform)
        reset_response = self.client.post(
            f"/api/v1/users/users/{self.school_admin.id}/reset-password/",
            {"new_password": "NewStrongPass123!"},
            format="json",
        )
        self.assertEqual(reset_response.status_code, status.HTTP_200_OK)

        token_response = self.client.post(
            "/api/v1/auth/token/",
            {"email": self.school_admin.email, "password": "NewStrongPass123!"},
            format="json",
        )
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)

    def test_me_endpoint_returns_connected_user(self):
        self.client.force_authenticate(user=self.platform)
        response = self.client.get("/api/v1/users/users/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.platform.email)
        self.assertEqual(response.data["role"], "PLATFORM_SUPERADMIN")

    def test_school_admin_cannot_create_membership_for_other_school(self):
        self.client.force_authenticate(user=self.school_admin)
        response = self.client.post(
            "/api/v1/users/school-memberships/",
            {
                "school": str(self.school_b.id),
                "user": str(self.teacher_a.id),
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
