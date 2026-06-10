"""
Seed de démonstration pour le tableau de bord Enseignant.
Lancer: venv\\Scripts\\python.exe manage.py shell -c "exec(open('seed_teacher_demo.py', encoding='utf-8').read())"
Compte: teacher01@example.com / StrongPass123!
"""
from django.utils import timezone
from django.contrib.auth import get_user_model

from users.models import School, SchoolMembership
from sis.models import Student, Classroom, Attendance
from pcs.models import Course, Chapter, Resource

User = get_user_model()

# --- École -----------------------------------------------------------------
school, _ = School.objects.get_or_create(
    code="DEMO-MOR",
    defaults={"name": "Collège de Moroni", "is_active": True},
)
school.name = "Collège de Moroni"
school.is_active = True
school.save()

# --- Enseignant ------------------------------------------------------------
teacher, _ = User.objects.get_or_create(
    email="teacher01@example.com",
    defaults={"username": "demo_teacher"},
)
teacher.username = teacher.username or "demo_teacher"
teacher.role = "TEACHER"
teacher.first_name = "Anrafa"
teacher.last_name = "Saïd"
teacher.default_school = school
teacher.is_active = True
teacher.set_password("StrongPass123!")
teacher.save()
SchoolMembership.objects.update_or_create(
    school=school, user=teacher, defaults={"is_active": True}
)

# --- Classes + élèves ------------------------------------------------------
YEAR = "2025-2026"
ROSTERS = {
    "3ème A": [
        "Halima Abdou", "Said Mohamed", "Faïza Ali", "Nadjib Combo",
        "Zalifa Hamid", "Ahmed Bacar", "Mariama Soulé", "Ibrahim Toﬃq",
        "Echata Madi", "Rachid Anli",
    ],
    "4ème B": [
        "Soifia Ahamada", "Nasser Djoumoi", "Aïcha Ousseni", "Bourhane Said",
        "Maoulida Ali", "Hadidja Mze", "Youssouf Hamadi",
    ],
    "6ème C": [
        "Inaya Abdallah", "Karim Mhoma", "Salima Bacar", "Daniel Mlanao",
        "Fatima Soulaimana", "Antoy Combo",
    ],
}

counter = 1
for class_name, names in ROSTERS.items():
    classroom, _ = Classroom.objects.get_or_create(
        school=school,
        name=class_name,
        academic_year=YEAR,
    )
    students = []
    for full_name in names:
        first, _, last = full_name.partition(" ")
        matricule = f"DEMO-{counter:04d}"
        counter += 1
        email = f"eleve{matricule.lower()}@demo.km"
        su, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": f"demo_{matricule.lower()}"},
        )
        su.role = "STUDENT"
        su.first_name = first
        su.last_name = last
        su.default_school = school
        su.is_active = True
        su.save()
        student, _ = Student.objects.get_or_create(
            user=su, defaults={"school": school, "matricule": matricule}
        )
        student.school = school
        student.matricule = student.matricule or matricule
        student.save()
        students.append(student)
    classroom.students.set(students)

# --- Cours progressif de l'enseignant --------------------------------------
classroom_3a = Classroom.objects.filter(school=school, name="3ème A").first()
course, _ = Course.objects.get_or_create(
    teacher=teacher,
    title="Mathématiques 3ème",
    defaults={"description": "Programme de mathématiques — classe d'examen.", "classroom": classroom_3a},
)
course.classroom = classroom_3a
course.save()

chapters_spec = [
    ("Nombres et calculs", "UNLOCKED"),
    ("Fractions et proportions", "UNLOCKED"),
    ("Théorème de Pythagore", "LOCKED"),
    ("Statistiques", "LOCKED"),
]
for order, (title, status) in enumerate(chapters_spec, start=1):
    chapter, _ = Chapter.objects.get_or_create(
        course=course, title=title, defaults={"order": order, "status": status}
    )
    chapter.order = order
    chapter.status = status
    chapter.save()
    Resource.objects.get_or_create(
        chapter=chapter,
        title=f"Fiche — {title}",
        defaults={"type": "PDF", "url": "", "status": status},
    )

# --- Quelques présences du jour (3ème A) -----------------------------------
now = timezone.now()
roster_3a = list(classroom_3a.students.all()) if classroom_3a else []
for student, status in zip(roster_3a, ["ABSENT", "LATE", "ABSENT"]):
    Attendance.objects.update_or_create(
        student=student,
        date=now,
        defaults={"status": status, "is_synced": True},
    )

print("seed_teacher_demo_ok:",
      "school=", school.code,
      "classes=", Classroom.objects.filter(school=school).count(),
      "students=", Student.objects.filter(school=school).count())
