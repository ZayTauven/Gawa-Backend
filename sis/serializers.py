from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Attendance, Classroom, LiaisonNote, Student, TimetableSlot
from users.models import SchoolMembership


class StudentSerializer(serializers.ModelSerializer):
    user = serializers.UUIDField(source="user_id")
    parent_user = serializers.UUIDField(source="parent_user_id", allow_null=True, required=False)
    school = serializers.UUIDField(source="school_id", allow_null=True, required=False)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "school",
            "user",
            "parent_user",
            "matricule",
            "first_name",
            "last_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "first_name", "last_name", "created_at", "updated_at"]

class StudentSummarySerializer(serializers.ModelSerializer):
    """Vue allégée d'un élève pour l'affichage des effectifs de classe (appel)."""

    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "matricule", "first_name", "last_name"]


class ClassroomSerializer(serializers.ModelSerializer):
    students = StudentSummarySerializer(many=True, read_only=True)
    student_count = serializers.IntegerField(source="students.count", read_only=True)

    class Meta:
        model = Classroom
        fields = ['id', 'school', 'name', 'academic_year', 'students', 'student_count', 'created_at', 'updated_at']
        read_only_fields = ['students', 'student_count', 'created_at', 'updated_at']

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'status', 'date', 'is_synced', 'created_at', 'updated_at']

class LiaisonNoteSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)

    class Meta:
        model = LiaisonNote
        fields = ['id', 'student', 'teacher', 'teacher_name', 'content', 'parent_acknowledged', 'created_at', 'updated_at']


class TimetableSlotSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.get_full_name", read_only=True)
    school_code = serializers.CharField(source="school.code", read_only=True)
    day_label = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model = TimetableSlot
        fields = [
            "id",
            "school",
            "school_code",
            "classroom",
            "classroom_name",
            "teacher",
            "teacher_name",
            "day_of_week",
            "day_label",
            "start_time",
            "end_time",
            "subject",
            "room",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "school_code",
            "classroom_name",
            "teacher_name",
            "day_label",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        classroom = attrs.get("classroom") or getattr(self.instance, "classroom", None)
        teacher = attrs.get("teacher", getattr(self.instance, "teacher", None))
        school = attrs.get("school", getattr(self.instance, "school", None))
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "L'heure de fin doit etre apres l'heure de debut."})

        if school is None and classroom is not None:
            school = classroom.school
            attrs["school"] = school

        if classroom is None:
            raise serializers.ValidationError({"classroom": "La classe est obligatoire."})

        if school is None:
            raise serializers.ValidationError({"school": "L'ecole est obligatoire."})

        if classroom.school_id and classroom.school_id != school.id:
            raise serializers.ValidationError({"classroom": "La classe doit appartenir a la meme ecole."})

        if teacher is not None:
            user_model = get_user_model()
            if not isinstance(teacher, user_model):
                raise serializers.ValidationError({"teacher": "Enseignant invalide."})
            teacher_school_match = getattr(teacher, "default_school_id", None) == school.id
            teacher_membership_match = SchoolMembership.objects.filter(
                user=teacher,
                school=school,
                is_active=True,
            ).exists()
            if not (teacher_school_match or teacher_membership_match):
                raise serializers.ValidationError({"teacher": "L'enseignant doit appartenir a la meme ecole."})

        return attrs
