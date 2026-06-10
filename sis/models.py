import uuid
from django.db import models
from django.conf import settings

class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    school = models.ForeignKey('users.School', on_delete=models.CASCADE, related_name='students', null=True, blank=True)
    matricule = models.CharField(max_length=50, unique=True)
    parent_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.matricule})"

class Classroom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey('users.School', on_delete=models.CASCADE, related_name='classrooms', null=True, blank=True)
    name = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=20)
    students = models.ManyToManyField(Student, related_name='classrooms')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.academic_year})"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    date = models.DateTimeField()
    is_synced = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.status} on {self.date}"

class LiaisonNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='liaison_notes')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='written_notes')
    content = models.TextField()
    parent_acknowledged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)


class TimetableSlot(models.Model):
    DAY_CHOICES = (
        (1, "Monday"),
        (2, "Tuesday"),
        (3, "Wednesday"),
        (4, "Thursday"),
        (5, "Friday"),
        (6, "Saturday"),
        (7, "Sunday"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "users.School",
        on_delete=models.CASCADE,
        related_name="timetable_slots",
        null=True,
        blank=True,
    )
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="timetable_slots")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="timetable_slots",
        null=True,
        blank=True,
    )
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.CharField(max_length=200)
    room = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ["day_of_week", "start_time", "classroom__name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="sis_timetable_slot_end_after_start",
            )
        ]

    def __str__(self):
        return f"{self.classroom.name} - {self.subject} ({self.day_of_week})"
