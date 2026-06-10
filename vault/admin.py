from django.contrib import admin
from .models import SealedArchive, ArchiveAccessLog

@admin.register(SealedArchive)
class SealedArchiveAdmin(admin.ModelAdmin):
    list_display = ('student_matricule', 'academic_year', 'sealed_at', 'sealed_by')
    list_filter = ('academic_year', 'sealed_at')

@admin.register(ArchiveAccessLog)
class ArchiveAccessLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'admin_email', 'timestamp', 'ip_address')
    list_filter = ('action_type', 'timestamp')
