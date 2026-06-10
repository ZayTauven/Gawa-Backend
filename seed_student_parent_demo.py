"""
Seed démo pour les espaces Élève et Parent (école DEMO-MOR).
Lancer: venv\\Scripts\\python.exe manage.py shell -c "exec(open('seed_student_parent_demo.py', encoding='utf-8').read())"
Comptes: eleve@demo-mor.km / StrongPass123!   et   parent@demo-mor.km / StrongPass123!
"""
import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model

from users.models import School, SchoolMembership
from sis.models import Student, Attendance, LiaisonNote
from pcs.models import Course, Chapter
from exam.models import Quiz, Question, Choice, StudentAttempt
from finance.models import BroadcastMessage

User = get_user_model()
school = School.objects.get(code="DEMO-MOR")
teacher = User.objects.get(email="teacher01@example.com")

# --- Élève (login propre sur un élève existant) ----------------------------
s1 = Student.objects.get(matricule="DEMO-0001")
s2 = Student.objects.get(matricule="DEMO-0002")

su = s1.user
su.email = "eleve@demo-mor.km"
su.role = "STUDENT"
su.default_school = school
su.is_active = True
su.set_password("StrongPass123!")
su.save()
SchoolMembership.objects.update_or_create(school=school, user=su, defaults={"is_active": True})

# --- Parent (rattaché à 2 enfants) -----------------------------------------
parent, _ = User.objects.get_or_create(email="parent@demo-mor.km", defaults={"username": "demo_parent"})
parent.username = parent.username or "demo_parent"
parent.role = "PARENT"
parent.first_name = "Halima"
parent.last_name = "Abdou"
parent.default_school = school
parent.is_active = True
parent.set_password("StrongPass123!")
parent.save()
SchoolMembership.objects.update_or_create(school=school, user=parent, defaults={"is_active": True})
for st in (s1, s2):
    st.parent_user = parent
    st.save()

# --- Quiz publiés + résultats de l'élève -----------------------------------
course = Course.objects.filter(teacher=teacher, title="Mathématiques 3ème").first()
chapters = list(Chapter.objects.filter(course=course).order_by("order")) if course else []

def make_quiz(chapter, title, qa):
    quiz, _ = Quiz.objects.get_or_create(chapter=chapter, title=title, defaults={"status": "PUBLISHED"})
    quiz.status = "PUBLISHED"
    quiz.save()
    for text, options in qa:
        q, _ = Question.objects.get_or_create(quiz=quiz, text=text, defaults={"source_reference": "Programme 3ème"})
        for opt_text, correct in options:
            Choice.objects.get_or_create(question=q, text=opt_text, defaults={"is_correct": correct})
    return quiz

if len(chapters) >= 2:
    quiz1 = make_quiz(chapters[0], "Quiz — Nombres et calculs", [
        ("Combien font 7 x 8 ?", [("54", False), ("56", True), ("48", False)]),
        ("Le PGCD de 12 et 18 ?", [("6", True), ("3", False), ("9", False)]),
    ])
    quiz2 = make_quiz(chapters[1], "Quiz — Fractions", [
        ("1/2 + 1/4 = ?", [("3/4", True), ("2/6", False), ("1/6", False)]),
    ])
    StudentAttempt.objects.get_or_create(student=s1, quiz=quiz1, defaults={"score": 85})
    StudentAttempt.objects.get_or_create(student=s1, quiz=quiz2, defaults={"score": 68})

# --- Présences de l'élève --------------------------------------------------
now = timezone.now()
Attendance.objects.update_or_create(student=s1, date=now - datetime.timedelta(days=2), defaults={"status": "LATE", "is_synced": True})
Attendance.objects.update_or_create(student=s1, date=now - datetime.timedelta(days=5), defaults={"status": "ABSENT", "is_synced": True})

# --- Carnet de liaison -----------------------------------------------------
LiaisonNote.objects.get_or_create(
    student=s1, teacher=teacher,
    content="Très bonne participation cette semaine, continue ainsi.",
    defaults={"parent_acknowledged": True},
)
LiaisonNote.objects.get_or_create(
    student=s1, teacher=teacher,
    content="Devoir de mathématiques non rendu, merci de vérifier le cahier.",
    defaults={"parent_acknowledged": False},
)
LiaisonNote.objects.get_or_create(
    student=s2, teacher=teacher,
    content="Bel exposé présenté en classe aujourd'hui.",
    defaults={"parent_acknowledged": False},
)

# --- Annonce école ---------------------------------------------------------
BroadcastMessage.objects.get_or_create(
    school=school, title="Réunion parents-professeurs",
    defaults={"content": "La réunion se tiendra samedi prochain à 9h dans la cour de l'école.", "target_audience": "ALL", "sent_by": teacher},
)

print("seed_student_parent_demo_ok:",
      "student=", su.email,
      "parent=", parent.email,
      "children=", Student.objects.filter(parent_user=parent).count(),
      "attempts=", StudentAttempt.objects.filter(student=s1).count(),
      "notes=", LiaisonNote.objects.filter(student__in=[s1, s2]).count())
