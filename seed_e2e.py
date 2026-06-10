from django.contrib.auth import get_user_model
from users.models import School, SchoolMembership
from sis.models import Student
from pcs.models import Course, Chapter, Resource
from exam.models import Quiz, Question, Choice

User = get_user_model()
school, _ = School.objects.get_or_create(code='E2E-SCH', defaults={'name':'E2E School','is_active':True})
school.name = 'E2E School'
school.is_active = True
school.save()

platform, _ = User.objects.get_or_create(email='platform@gawa.local', defaults={'username':'e2e_platform','role':'PLATFORM_SUPERADMIN','is_active':True})
platform.role = 'PLATFORM_SUPERADMIN'
platform.is_active = True
platform.set_password('StrongPass123!')
platform.save()

teacher, _ = User.objects.get_or_create(email='teacher01@example.com', defaults={'username':'e2e_teacher'})
teacher.username = teacher.username or 'e2e_teacher'
teacher.role = 'TEACHER'
teacher.default_school = school
teacher.first_name = 'E2E'
teacher.last_name = 'Teacher'
teacher.is_active = True
teacher.set_password('StrongPass123!')
teacher.save()

student_user, _ = User.objects.get_or_create(email='student01@example.com', defaults={'username':'e2e_student'})
student_user.username = student_user.username or 'e2e_student'
student_user.role = 'STUDENT'
student_user.default_school = school
student_user.first_name = 'E2E'
student_user.last_name = 'Student'
student_user.is_active = True
student_user.set_password('StrongPass123!')
student_user.save()

for u in [platform, teacher, student_user]:
    SchoolMembership.objects.update_or_create(school=school, user=u, defaults={'is_active':True})

student, _ = Student.objects.get_or_create(user=student_user, defaults={'school':school,'matricule':'E2E-STU-001'})
student.school = school
if not student.matricule:
    student.matricule = 'E2E-STU-001'
student.save()

course, _ = Course.objects.get_or_create(teacher=teacher, title='E2E Histoire', defaults={'description':'Cours E2E','classroom':None})
chapter, _ = Chapter.objects.get_or_create(course=course, title='Chapitre E2E', defaults={'order':1,'status':'UNLOCKED'})
chapter.status = 'UNLOCKED'
chapter.save()
Resource.objects.get_or_create(chapter=chapter, title='Ressource E2E', defaults={'type':'TEXT','url':'','status':'UNLOCKED'})
quiz, _ = Quiz.objects.get_or_create(chapter=chapter, title='Quiz E2E', defaults={'status':'PUBLISHED'})
quiz.status = 'PUBLISHED'
quiz.save()
question, _ = Question.objects.get_or_create(quiz=quiz, text='Quelle est la date symbolique?', defaults={'source_reference':'E2E source'})
Choice.objects.update_or_create(question=question, text='6 Juillet 1975', defaults={'is_correct':True})
Choice.objects.update_or_create(question=question, text='1 Janvier 2000', defaults={'is_correct':False})
Choice.objects.update_or_create(question=question, text='14 Juillet 1789', defaults={'is_correct':False})
print('seed_e2e_ok')
