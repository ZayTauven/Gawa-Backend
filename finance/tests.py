from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from finance.models import Invoice, Payment
from sis.models import Student
from users.models import School


class FinanceApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.school = School.objects.create(code="SCH-FIN", name="School Finance")
        self.admin = user_model.objects.create_user(
            username="adminfinance",
            email="adminfinance@example.com",
            password="StrongPass123!",
            role="ADMIN",
            default_school=self.school,
        )
        self.parent = user_model.objects.create_user(
            username="parentfinance",
            email="parentfinance@example.com",
            password="StrongPass123!",
            role="PARENT",
            default_school=self.school,
        )
        self.student_user = user_model.objects.create_user(
            username="studentfinance",
            email="studentfinance@example.com",
            password="StrongPass123!",
            role="STUDENT",
            default_school=self.school,
        )
        self.other_student_user = user_model.objects.create_user(
            username="studentfinance2",
            email="studentfinance2@example.com",
            password="StrongPass123!",
            role="STUDENT",
            default_school=self.school,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            school=self.school,
            parent_user=self.parent,
            matricule="MAT-FIN-001",
        )
        self.other_student = Student.objects.create(
            user=self.other_student_user,
            school=self.school,
            matricule="MAT-FIN-002",
        )

        self.invoice = Invoice.objects.create(
            student=self.student,
            amount="50000.00",
            due_date=date.today() + timedelta(days=10),
            status="PENDING",
            invoice_period="2025-2026-T1",
        )
        Invoice.objects.create(
            student=self.other_student,
            amount="60000.00",
            due_date=date.today() + timedelta(days=10),
            status="PENDING",
            invoice_period="2025-2026-T1",
        )

    def test_student_list_invoices_returns_only_own(self):
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get("/api/v1/finance/invoices/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(str(response.data[0]["student"]), str(self.student.id))

    def test_payment_create_sets_recorded_by_connected_admin(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "invoice": str(self.invoice.id),
            "amount_paid": "25000.00",
            "payment_method": "CASH",
            "recorded_by": str(self.parent.id),
        }

        response = self.client.post("/api/v1/finance/payments/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(id=response.data["id"])
        self.assertEqual(payment.recorded_by_id, self.admin.id)
