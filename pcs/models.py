import uuid
from django.db import models
from django.conf import settings
from sis.models import Classroom
from django.utils import timezone

class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, null=True, related_name='courses')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.title

class Chapter(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('LOCKED', 'Locked'),
        ('UNLOCKED', 'Unlocked'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='LOCKED')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Resource(models.Model):
    TYPE_CHOICES = (
        ('PDF', 'PDF Document'),
        ('LINK', 'External Link'),
        ('TEXT', 'Rich Text'),
        ('IMAGE', 'Image'),
    )
    STATUS_CHOICES = (
        ('LOCKED', 'Locked'),
        ('UNLOCKED', 'Unlocked'),
    )
    DOCUMENT_CLASS_CHOICES = (
        ("PUBLIC_RESOURCE", "Public Resource"),
        ("SCHOOL_COMMUNICATION", "School Communication"),
        ("PEDAGOGICAL_RESTRICTED", "Pedagogical Restricted"),
        ("OFFICIAL_ARCHIVE_VAULT", "Official Archive Vault"),
        ("AI_TRAINING_CORPUS", "AI Training Corpus"),
    )
    AUDIENCE_CHOICES = (
        ("STUDENT", "Student"),
        ("PARENT", "Parent"),
        ("TEACHER", "Teacher"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    url = models.CharField(max_length=500, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='LOCKED')
    document_class = models.CharField(
        max_length=32,
        choices=DOCUMENT_CLASS_CHOICES,
        default="PEDAGOGICAL_RESTRICTED",
    )
    target_audiences = models.JSONField(default=list, blank=True)
    ai_eligible = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def save(self, *args, **kwargs):
        if self.status == "UNLOCKED" and self.published_at is None:
            self.published_at = timezone.now()
        if self.status == "LOCKED" and self.document_class == "OFFICIAL_ARCHIVE_VAULT":
            # Prevent accidental publication flow for vault-only documents.
            self.ai_eligible = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
