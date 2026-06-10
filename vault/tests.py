from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import School
from vault.models import SealedArchive


class VaultTenantTests(APITestCase):
    databases = {"default", "archive_db"}

    def setUp(self):
        user_model = get_user_model()
        self.school_a = School.objects.create(code="SCH-A", name="School A")
        self.school_b = School.objects.create(code="SCH-B", name="School B")

        self.platform = user_model.objects.create_user(
            username="platformvault",
            email="platformvault@example.com",
            password="StrongPass123!",
            role="PLATFORM_SUPERADMIN",
        )
        self.school_admin = user_model.objects.create_user(
            username="schooladminvault",
            email="schooladminvault@example.com",
            password="StrongPass123!",
            role="SCHOOL_ADMIN",
            default_school=self.school_a,
        )

        SealedArchive.objects.using("archive_db").create(
            school_code=self.school_a.code,
            student_matricule="MAT-A-001",
            academic_year="2025-2026",
            encrypted_document_url="https://example.com/a1.enc",
            file_hash_sha256="a" * 64,
            sealed_by="admin-a@example.com",
        )
        SealedArchive.objects.using("archive_db").create(
            school_code=self.school_b.code,
            student_matricule="MAT-B-001",
            academic_year="2025-2026",
            encrypted_document_url="https://example.com/b1.enc",
            file_hash_sha256="b" * 64,
            sealed_by="admin-b@example.com",
        )

    def test_school_admin_sees_only_its_school_archives(self):
        self.client.force_authenticate(user=self.school_admin)
        response = self.client.get("/api/v1/vault/archives/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["school_code"], self.school_a.code)

    def test_platform_with_school_header_filters_archives(self):
        self.client.force_authenticate(user=self.platform)
        response = self.client.get(
            "/api/v1/vault/archives/",
            HTTP_X_SCHOOL_ID=str(self.school_b.id),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["school_code"], self.school_b.code)
