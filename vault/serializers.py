from rest_framework import serializers
from .models import SealedArchive, ArchiveAccessLog

class SealedArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = SealedArchive
        fields = ['id', 'school_code', 'student_matricule', 'academic_year', 'encrypted_document_url', 'file_hash_sha256', 'sealed_at', 'sealed_by']
        read_only_fields = ['school_code', 'sealed_at']

class ArchiveAccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchiveAccessLog
        fields = ['id', 'school_code', 'action_type', 'admin_email', 'target_matricule', 'timestamp', 'ip_address']
        read_only_fields = ['school_code', 'admin_email', 'timestamp', 'ip_address']
