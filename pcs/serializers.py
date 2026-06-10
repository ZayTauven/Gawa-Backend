from rest_framework import serializers
from .models import Course, Chapter, Resource

ALLOWED_AI_CLASSES = {
    "PUBLIC_RESOURCE",
    "PEDAGOGICAL_RESTRICTED",
    "AI_TRAINING_CORPUS",
}


class ResourceSerializer(serializers.ModelSerializer):
    chapter_title = serializers.CharField(source="chapter.title", read_only=True)

    class Meta:
        model = Resource
        fields = [
            "id",
            "chapter",
            "chapter_title",
            "title",
            "type",
            "url",
            "size_bytes",
            "status",
            "document_class",
            "target_audiences",
            "ai_eligible",
            "published_at",
            "unlocked_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "chapter_title"]

    def validate_target_audiences(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("target_audiences doit etre une liste.")

        allowed = {choice[0] for choice in Resource.AUDIENCE_CHOICES}
        normalized = []
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("Chaque audience doit etre une chaine.")
            upper_item = item.upper()
            if upper_item not in allowed:
                raise serializers.ValidationError(f"Audience invalide: {item}")
            if upper_item not in normalized:
                normalized.append(upper_item)
        return normalized

    def validate(self, attrs):
        document_class = attrs.get("document_class")
        if document_class is None and self.instance is not None:
            document_class = self.instance.document_class

        ai_eligible = attrs.get("ai_eligible")
        if ai_eligible is None and self.instance is not None:
            ai_eligible = self.instance.ai_eligible

        target_audiences = attrs.get("target_audiences")
        if target_audiences is None and self.instance is not None:
            target_audiences = self.instance.target_audiences

        if self.instance is None and not target_audiences and document_class == "PEDAGOGICAL_RESTRICTED":
            attrs["target_audiences"] = ["STUDENT"]
            target_audiences = attrs["target_audiences"]

        if document_class == "OFFICIAL_ARCHIVE_VAULT":
            raise serializers.ValidationError(
                {"document_class": "Les archives officielles doivent etre deposees via Vault (/api/v1/vault/archives/)."}
            )

        if ai_eligible and document_class not in ALLOWED_AI_CLASSES:
            raise serializers.ValidationError(
                {"ai_eligible": "Seules les ressources pedagogiques peuvent etre eligibles IA."}
            )

        if document_class in {"PUBLIC_RESOURCE", "SCHOOL_COMMUNICATION", "AI_TRAINING_CORPUS"}:
            if not target_audiences:
                raise serializers.ValidationError(
                    {"target_audiences": "Au moins une audience est requise pour ce type de document."}
                )

        return attrs


class ChapterSerializer(serializers.ModelSerializer):
    resources = ResourceSerializer(many=True, read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Chapter
        fields = [
            "id",
            "course",
            "course_title",
            "title",
            "order",
            "status",
            "resources",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["course_title", "resources", "created_at", "updated_at"]


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.get_full_name", read_only=True)
    teacher = serializers.UUIDField(source="teacher_id", read_only=True)
    chapter_count = serializers.IntegerField(source="chapters.count", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "teacher",
            "classroom",
            "title",
            "description",
            "teacher_name",
            "chapter_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["teacher", "teacher_name", "chapter_count", "created_at", "updated_at"]
