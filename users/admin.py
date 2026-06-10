from django.contrib import admin
from .models import School, SchoolMembership, User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'default_school', 'is_staff')
    list_filter = ('role', 'default_school', 'is_staff', 'is_active')
    search_fields = ('username', 'email')


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(SchoolMembership)
class SchoolMembershipAdmin(admin.ModelAdmin):
    list_display = ('school', 'user', 'is_active', 'created_at')
    list_filter = ('school', 'is_active')
    search_fields = ('school__name', 'school__code', 'user__email', 'user__username')
