import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gawa_core.settings')
django.setup()

from sis.models import Student
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a teacher
teacher, _ = User.objects.get_or_create(
    email='teacher1@ecole.km', 
    defaults={'username': 'teacher1', 'role': 'TEACHER'}
)
teacher.set_password('password123')
teacher.save()

# Create students
students_data = [
    ('GAWA-001', 'moussa@student.km', 'Moussa', 'Ali'),
    ('GAWA-002', 'fatima@student.km', 'Fatima', 'Said'),
    ('GAWA-003', 'ahmed@student.km', 'Ahmed', 'Abdou'),
    ('GAWA-004', 'zahra@student.km', 'Zahra', 'Hassan'),
]

for mat, email, first, last in students_data:
    user, _ = User.objects.get_or_create(
        email=email, 
        defaults={'username': mat, 'role': 'STUDENT', 'first_name': first, 'last_name': last}
    )
    Student.objects.get_or_create(user=user, matricule=mat)

print(f"Created {len(students_data)} students.")
