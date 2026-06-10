"""
Seed démo pour le dashboard Admin d'établissement (SCHOOL_ADMIN) de DEMO-MOR.
Lancer: venv\\Scripts\\python.exe manage.py shell -c "exec(open('seed_admin_demo.py', encoding='utf-8').read())"
Compte: admin@demo-mor.km / StrongPass123!
"""
import datetime
from decimal import Decimal

from django.utils import timezone
from django.contrib.auth import get_user_model

from users.models import School, SchoolMembership
from sis.models import Student
from finance.models import Invoice

User = get_user_model()

school = School.objects.get(code="DEMO-MOR")

admin, _ = User.objects.get_or_create(
    email="admin@demo-mor.km",
    defaults={"username": "demo_admin_mor"},
)
admin.username = admin.username or "demo_admin_mor"
admin.role = "SCHOOL_ADMIN"
admin.first_name = "Ibrahim"
admin.last_name = "Mhadji"
admin.default_school = school
admin.is_active = True
admin.set_password("StrongPass123!")
admin.save()
SchoolMembership.objects.update_or_create(school=school, user=admin, defaults={"is_active": True})

# Factures variées pour les élèves de DEMO-MOR
students = list(Student.objects.filter(school=school).order_by("matricule"))
today = timezone.now().date()
cycle = [
    ("OVERDUE", -25), ("OVERDUE", -12), ("PENDING", 8), ("PAID", -30),
    ("PARTIAL", 3), ("PAID", -10), ("OVERDUE", -5), ("PENDING", 20),
]
for idx, student in enumerate(students):
    status, offset = cycle[idx % len(cycle)]
    Invoice.objects.update_or_create(
        student=student,
        invoice_period="2025-T1",
        defaults={
            "amount": Decimal("45000.00"),
            "due_date": today + datetime.timedelta(days=offset),
            "status": status,
        },
    )

print(
    "seed_admin_demo_ok:",
    "admin=", admin.email,
    "students=", len(students),
    "invoices=", Invoice.objects.filter(student__school=school).count(),
    "overdue=", Invoice.objects.filter(student__school=school, status="OVERDUE").count(),
)
