from rest_framework import serializers

from .models import Choice, Question, Quiz, StudentAttempt

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "question", "text", "is_correct"]

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "quiz", "text", "source_reference", "choices"]

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "chapter", "title", "status", "questions"]

class StudentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAttempt
        fields = ["id", "student", "quiz", "score", "completed_at"]
        read_only_fields = ["id", "completed_at"]


class HibouGenerateQuizRequestSerializer(serializers.Serializer):
    resource_id = serializers.UUIDField(required=False)
    chapter_id = serializers.UUIDField(required=False)
    number_of_questions = serializers.IntegerField(min_value=1, max_value=20, default=5)
    difficulty = serializers.ChoiceField(choices=["EASY", "MEDIUM", "HARD"], default="MEDIUM")

    def validate(self, attrs):
        if not attrs.get("resource_id") and not attrs.get("chapter_id"):
            raise serializers.ValidationError("resource_id ou chapter_id est requis.")
        return attrs


class StudentQuizAnswerInputSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    choice_id = serializers.UUIDField()


class StudentQuizSubmitSerializer(serializers.Serializer):
    answers = StudentQuizAnswerInputSerializer(many=True, min_length=1)


class ApprovedChoiceInputSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=1000)
    is_correct = serializers.BooleanField(default=False)


class ApprovedQuestionInputSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=4000)
    source_reference = serializers.CharField(required=False, allow_blank=True, max_length=255)
    choices = ApprovedChoiceInputSerializer(many=True, min_length=2)

    def validate_choices(self, value):
        if sum(1 for item in value if item.get("is_correct")) != 1:
            raise serializers.ValidationError("Chaque question doit avoir exactement une bonne reponse.")
        return value


class CreateApprovedQuizSerializer(serializers.Serializer):
    chapter_id = serializers.UUIDField()
    title = serializers.CharField(max_length=200)
    status = serializers.ChoiceField(choices=["DRAFT", "PUBLISHED"], default="DRAFT")
    questions = ApprovedQuestionInputSerializer(many=True, min_length=1, max_length=50)
