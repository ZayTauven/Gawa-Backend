"""
Seed de démonstration pour la console Pilotage (superadmin plateforme).
Lancer: venv\\Scripts\\python.exe manage.py shell -c "exec(open('seed_platform_demo.py', encoding='utf-8').read())"
Compte: platform@gawa.local / StrongPass123!  (vue globale, sans default_school)
"""
import datetime
from decimal import Decimal

from django.utils import timezone
from django.contrib.auth import get_user_model

from users.models import School
from sis.models import Student
from finance.models import Invoice
from vault.models import ArchiveAccessLog

User = get_user_model()

# --- Superadmin plateforme (vue globale) -----------------------------------
platform, _ = User.objects.get_or_create(
    email="platform@gawa.local",
    defaults={"username": "demo_platform"},
)
platform.username = platform.username or "demo_platform"
platform.role = "PLATFORM_SUPERADMIN"
platform.first_name = "Nadia"
platform.last_name = "Pilote"
platform.default_school = None  # pas de scope école => agrégat global
platform.is_active = True
platform.set_password("StrongPass123!")
platform.save()

# --- Écoles du réseau ------------------------------------------------------
School.objects.get_or_create(code="DEMO-MOR", defaults={"name": "Collège de Moroni", "is_active": True})
School.objects.update_or_create(code="LYC-MUT", defaults={"name": "Lycée de Mutsamudu", "is_active": True})
School.objects.update_or_create(code="ECO-FOM", defaults={"name": "École de Fomboni", "is_active": False})

# --- Factures (dont des impayées) ------------------------------------------
students = list(Student.objects.all()[:8])
today = timezone.now().date()
specs = [
    ("OVERDUE", -20), ("OVERDUE", -8), ("OVERDUE", -3),
    ("PENDING", 10), ("PENDING", 25), ("PAID", -5), ("PAID", -15), ("PARTIAL", 5),
]
for student, (status, offset) in zip(students, specs):
    Invoice.objects.update_or_create(
        student=student,
        invoice_period="2025-T1",
        defaults={
            "amount": Decimal("45000.00"),
            "due_date": today + datetime.timedelta(days=offset),
            "status": status,
        },
    )

# --- Journal d'accès aux archives (coffre-fort) ----------------------------
matricule = students[0].matricule if students else "DEMO-0001"
for action in ["SEAL", "DECRYPT", "PRINT"]:
    ArchiveAccessLog.objects.get_or_create(
        school_code="DEMO-MOR",
        action_type=action,
        admin_email="admin@demo-mor.km",
        target_matricule=matricule,
        defaults={"ip_address": "127.0.0.1"},
    )

print(
    "seed_platform_demo_ok:",
    "schools=", School.objects.count(),
    "overdue=", Invoice.objects.filter(status="OVERDUE").count(),
    "logs=", ArchiveAccessLog.objects.count(),
)
