from django.contrib import admin
from .models import Student, Classroom, Attendance, LiaisonNote

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'get_full_name')
    search_fields = ('matricule', 'user__first_name', 'user__last_name')
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Name'

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year')
    list_filter = ('academic_year',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'is_synced')
    list_filter = ('date', 'status', 'is_synced')

@admin.register(LiaisonNote)
class LiaisonNoteAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'created_at', 'parent_acknowledged')
    list_filter = ('parent_acknowledged', 'created_at')
