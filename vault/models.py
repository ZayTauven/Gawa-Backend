import uuid

from django.db import models


class SealedArchive(models.Model):
    """
    Annual official archives stored in the dedicated archive_db.
    No foreign key to academic data to preserve strict DB isolation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_code = models.CharField(max_length=50, db_index=True, blank=True, default="")
    student_matricule = models.CharField(max_length=50, db_index=True)
    academic_year = models.CharField(max_length=20)
    encrypted_document_url = models.CharField(max_length=500)
    file_hash_sha256 = models.CharField(max_length=64)
    sealed_at = models.DateTimeField(auto_now_add=True)
    sealed_by = models.CharField(max_length=255)  # Admin email

    def __str__(self):
        return f"Archive {self.academic_year} {self.student_matricule}"


class ArchiveAccessLog(models.Model):
    ACTION_CHOICES = (
        ("SEAL", "Sealed Year"),
        ("DECRYPT", "Decrypted Archive"),
        ("PRINT", "Printed Archive"),
        ("FAILED_ATTEMPT", "Failed Access Attempt"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_code = models.CharField(max_length=50, db_index=True, blank=True, default="")
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    admin_email = models.CharField(max_length=255)
    target_matricule = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.action_type} by {self.admin_email}"
