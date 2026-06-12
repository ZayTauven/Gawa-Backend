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
    CATEGORY_CHOICES = (
        ('ANNALES', 'Annales'),
        ('CORRECTION', 'Corrigé'),
        ('NOTES', 'Notes de cours'),
        ('APPROFONDISSEMENT', 'Approfondissement'),
        ('OTHER', 'Autre'),
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
    # chapter facultatif : une ressource peut exister hors cours (partage autonome).
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE, related_name='resources', null=True, blank=True
    )
    # Classe cible d'une ressource AUTONOME (sans chapitre). Pour une ressource de
    # chapitre, la classe vient de chapter.course.classroom. classroom NULL = école entière.
    classroom = models.ForeignKey(
        Classroom, on_delete=models.CASCADE, related_name='resources', null=True, blank=True
    )
    # Auteur (créateur) : permet au prof de lister/gérer ses ressources autonomes.
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='authored_resources',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="OTHER",
        help_text="Taxonomie pédagogique : annales, corrigé, notes, approfondissement.",
    )
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
