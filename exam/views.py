from django.db import transaction
from django.db.models import Q
from rest_framework import status, viewsets, views
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from gawa_core.permissions import (
    ROLE_ADMIN,
    ROLE_PARENT,
    ROLE_PLATFORM_SUPERADMIN,
    ROLE_SCHOOL_ADMIN,
    ROLE_STUDENT,
    ROLE_TEACHER,
    RolePolicyPermission,
)
from gawa_core.tenancy import get_request_school, is_platform_superadmin
from pcs.models import Chapter, Resource
from sis.models import Student

from .models import Choice, Question, Quiz, StudentAttempt
from .serializers import (
    ChoiceSerializer,
    CreateApprovedQuizSerializer,
    HibouGenerateQuizRequestSerializer,
    QuestionSerializer,
    QuizSerializer,
    StudentAttemptSerializer,
    StudentQuizSubmitSerializer,
)

AI_ALLOWED_RESOURCE_CLASSES = {
    "PUBLIC_RESOURCE",
    "PEDAGOGICAL_RESTRICTED",
    "AI_TRAINING_CORPUS",
}

def _quiz_school_q(school):
    return (
        Q(chapter__course__classroom__school=school)
        | Q(chapter__course__classroom__isnull=True, chapter__course__teacher__default_school=school)
    )


def _chapter_school_q(school):
    return (
        Q(course__classroom__school=school)
        | Q(course__classroom__isnull=True, course__teacher__default_school=school)
    )


def _assert_chapter_in_scope(chapter: Chapter, user, school):
    role = getattr(user, "role", None)
    if is_platform_superadmin(user):
        if school and not Chapter.objects.filter(id=chapter.id).filter(_chapter_school_q(school)).exists():
            raise PermissionDenied("Chapitre hors scope ecole.")
        return

    if school is None:
        raise PermissionDenied("Contexte ecole requis.")

    in_scope = Chapter.objects.filter(id=chapter.id).filter(_chapter_school_q(school)).exists()
    if not in_scope:
        raise PermissionDenied("Chapitre hors scope ecole.")

    if role == ROLE_TEACHER and chapter.course.teacher_id != user.id:
        raise PermissionDenied("Vous pouvez generer des quiz uniquement sur vos cours.")


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_STUDENT,
        ROLE_PARENT,
    )
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        base_qs = Quiz.objects.select_related("chapter", "chapter__course", "chapter__course__teacher", "chapter__course__classroom")

        if is_platform_superadmin(user):
            if school:
                return base_qs.filter(_quiz_school_q(school)).distinct()
            return base_qs

        if school is None:
            return Quiz.objects.none()

        school_qs = base_qs.filter(_quiz_school_q(school)).distinct()
        if role == ROLE_TEACHER:
            return school_qs.filter(chapter__course__teacher=user)
        return school_qs


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_STUDENT,
        ROLE_PARENT,
    )
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        base_qs = Question.objects.select_related(
            "quiz",
            "quiz__chapter",
            "quiz__chapter__course",
            "quiz__chapter__course__teacher",
            "quiz__chapter__course__classroom",
        )

        if is_platform_superadmin(user):
            if school:
                return base_qs.filter(_quiz_school_q(school)).distinct()
            return base_qs

        if school is None:
            return Question.objects.none()

        school_qs = base_qs.filter(_quiz_school_q(school)).distinct()
        if role == ROLE_TEACHER:
            return school_qs.filter(quiz__chapter__course__teacher=user)
        return school_qs


class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_STUDENT,
        ROLE_PARENT,
    )
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        base_qs = Choice.objects.select_related(
            "question",
            "question__quiz",
            "question__quiz__chapter",
            "question__quiz__chapter__course",
            "question__quiz__chapter__course__teacher",
            "question__quiz__chapter__course__classroom",
        )

        if is_platform_superadmin(user):
            if school:
                return base_qs.filter(_quiz_school_q(school)).distinct()
            return base_qs

        if school is None:
            return Choice.objects.none()

        school_qs = base_qs.filter(_quiz_school_q(school)).distinct()
        if role == ROLE_TEACHER:
            return school_qs.filter(question__quiz__chapter__course__teacher=user)
        return school_qs


class StudentAttemptViewSet(viewsets.ModelViewSet):
    queryset = StudentAttempt.objects.all()
    serializer_class = StudentAttemptSerializer
    permission_classes = [RolePolicyPermission]
    read_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_STUDENT,
        ROLE_PARENT,
    )
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER, ROLE_STUDENT)

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        base_qs = StudentAttempt.objects.select_related("student", "student__user", "quiz", "quiz__chapter", "quiz__chapter__course")

        if is_platform_superadmin(user):
            if school:
                return base_qs.filter(student__school=school)
            return base_qs

        if school is None:
            return StudentAttempt.objects.none()

        school_qs = base_qs.filter(student__school=school)
        if role in {ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER}:
            return school_qs
        if role == ROLE_STUDENT:
            return school_qs.filter(student__user=user)
        if role == ROLE_PARENT:
            return school_qs.filter(student__parent_user=user)
        return StudentAttempt.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        role = getattr(user, "role", None)
        school = get_request_school(self.request)
        student = serializer.validated_data.get("student")

        if student is None:
            raise PermissionDenied("L'étudiant est requis.")

        if school and student.school_id != school.id:
            raise PermissionDenied("Étudiant hors scope école.")

        if role == ROLE_STUDENT and student.user_id != user.id:
            raise PermissionDenied("Vous ne pouvez enregistrer que vos propres tentatives.")
        serializer.save()


class HibouGenerateQuizView(views.APIView):
    permission_classes = [RolePolicyPermission]
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER)

    def post(self, request):
        serializer = HibouGenerateQuizRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        chapter = None
        resource = None
        if data.get("resource_id"):
            resource = Resource.objects.select_related("chapter", "chapter__course", "chapter__course__teacher").filter(
                id=data["resource_id"]
            ).first()
            if resource is None:
                raise ValidationError("resource_id introuvable.")
            if resource.status != "UNLOCKED":
                raise ValidationError("La ressource doit etre publiee pour etre exploitee par Hibou.")
            if resource.document_class not in AI_ALLOWED_RESOURCE_CLASSES or not resource.ai_eligible:
                raise ValidationError("La ressource n'est pas eligibile au corpus IA.")
            chapter = resource.chapter
        else:
            chapter = Chapter.objects.select_related("course", "course__teacher").filter(id=data["chapter_id"]).first()
            if chapter is None:
                raise ValidationError("chapter_id introuvable.")

        school = get_request_school(request)
        _assert_chapter_in_scope(chapter, request.user, school)

        if resource is None:
            ai_resource_qs = Resource.objects.filter(
                chapter=chapter,
                status="UNLOCKED",
                ai_eligible=True,
                document_class__in=AI_ALLOWED_RESOURCE_CLASSES,
            ).order_by("-updated_at")
            resource = ai_resource_qs.first()
            if resource is None:
                raise ValidationError(
                    "Aucune ressource IA eligibile publiee sur ce chapitre."
                )

        difficulty = data["difficulty"]
        count = data["number_of_questions"]
        course_title = chapter.course.title
        chapter_title = chapter.title
        resource_ref = resource.title

        question_stems = {
            "EASY": [
                "Quel est l'objectif principal de",
                "Quel element est explicitement presente dans",
                "Quelle affirmation decrit le mieux",
            ],
            "MEDIUM": [
                "Parmi les propositions, laquelle explique le mieux",
                "Quelle relation est correcte entre les notions de",
                "Quelle interpretation reste conforme a",
            ],
            "HARD": [
                "Quelle analyse critique est la plus coherente avec",
                "Quelle proposition evite une confusion frequente dans",
                "Quelle conclusion peut etre tiree en restant strictement dans",
            ],
        }
        distractors = [
            "Interpretation hors chapitre",
            "Detail non mentionne dans la ressource",
            "Generalisation non validee par le cours",
        ]

        generated_questions = []
        stems = question_stems[difficulty]
        for index in range(count):
            stem = stems[index % len(stems)]
            prompt_text = f"{stem} {chapter_title} ({course_title}) ?"
            correct_choice = f"Element conforme au contenu de {resource_ref}"
            generated_questions.append(
                {
                    "temp_id": f"hibou-{index + 1}",
                    "text": prompt_text,
                    "source_reference": f"{course_title} - {resource_ref}",
                    "choices": [
                        {"text": correct_choice, "is_correct": True},
                        {"text": distractors[(index + 0) % len(distractors)], "is_correct": False},
                        {"text": distractors[(index + 1) % len(distractors)], "is_correct": False},
                        {"text": distractors[(index + 2) % len(distractors)], "is_correct": False},
                    ],
                }
            )

        return Response(
            {
                "mode": "RAG_RESTRICTED_FALLBACK",
                "chapter_id": str(chapter.id),
                "resource_id": str(resource.id) if resource else None,
                "difficulty": difficulty,
                "questions": generated_questions,
            },
            status=status.HTTP_200_OK,
        )


class HibouCreateApprovedQuizView(views.APIView):
    permission_classes = [RolePolicyPermission]
    write_roles = (ROLE_PLATFORM_SUPERADMIN, ROLE_SCHOOL_ADMIN, ROLE_ADMIN, ROLE_TEACHER)

    @transaction.atomic
    def post(self, request):
        payload = CreateApprovedQuizSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        chapter = Chapter.objects.select_related("course", "course__teacher").filter(id=data["chapter_id"]).first()
        if chapter is None:
            raise ValidationError("chapter_id introuvable.")

        school = get_request_school(request)
        _assert_chapter_in_scope(chapter, request.user, school)

        quiz = Quiz.objects.create(chapter=chapter, title=data["title"], status=data["status"])
        for question_data in data["questions"]:
            question = Question.objects.create(
                quiz=quiz,
                text=question_data["text"],
                source_reference=question_data.get("source_reference", ""),
            )
            for choice_data in question_data["choices"]:
                Choice.objects.create(
                    question=question,
                    text=choice_data["text"],
                    is_correct=choice_data["is_correct"],
                )

        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)


class StudentQuizSubmitView(views.APIView):
    permission_classes = [RolePolicyPermission]
    write_roles = (ROLE_STUDENT,)

    @transaction.atomic
    def post(self, request, quiz_id):
        school = get_request_school(request)
        base_quiz_qs = Quiz.objects.select_related("chapter", "chapter__course", "chapter__course__teacher", "chapter__course__classroom")
        if school:
            base_quiz_qs = base_quiz_qs.filter(_quiz_school_q(school)).distinct()
        quiz = base_quiz_qs.filter(id=quiz_id, status="PUBLISHED").first()
        if quiz is None:
            raise ValidationError("Quiz introuvable ou non publie.")

        student = Student.objects.select_related("user").filter(user=request.user).first()
        if student is None:
            raise PermissionDenied("Profil etudiant introuvable.")
        if school and student.school_id != school.id:
            raise PermissionDenied("Etudiant hors scope ecole.")

        payload = StudentQuizSubmitSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        answers = payload.validated_data["answers"]

        questions = list(
            Question.objects.filter(quiz=quiz).prefetch_related("choices").all()
        )
        if not questions:
            raise ValidationError("Ce quiz ne contient aucune question.")

        answer_map = {}
        for item in answers:
            question_id = str(item["question_id"])
            if question_id in answer_map:
                raise ValidationError("Une question ne peut etre soumise qu'une seule fois.")
            answer_map[question_id] = str(item["choice_id"])

        question_ids = {str(q.id) for q in questions}
        if not set(answer_map.keys()).issubset(question_ids):
            raise ValidationError("Certaines questions ne correspondent pas a ce quiz.")

        total = len(questions)
        correct = 0
        details = []
        for question in questions:
            selected_choice_id = answer_map.get(str(question.id))
            correct_choice = next((c for c in question.choices.all() if c.is_correct), None)
            is_correct = bool(
                selected_choice_id and correct_choice and str(correct_choice.id) == selected_choice_id
            )
            if selected_choice_id and not any(str(c.id) == selected_choice_id for c in question.choices.all()):
                raise ValidationError("Une reponse reference un choix invalide pour la question.")
            if is_correct:
                correct += 1
            details.append(
                {
                    "question_id": str(question.id),
                    "is_correct": is_correct,
                    "source_reference": question.source_reference or "",
                }
            )

        score = round((correct / total) * 100)
        attempt = StudentAttempt.objects.create(student=student, quiz=quiz, score=score)

        return Response(
            {
                "attempt_id": str(attempt.id),
                "score": score,
                "correct_answers": correct,
                "total_questions": total,
                "details": details,
            },
            status=status.HTTP_201_CREATED,
        )


class HibouAskView(views.APIView):
    permission_classes = [RolePolicyPermission]
    write_roles = (
        ROLE_PLATFORM_SUPERADMIN,
        ROLE_SCHOOL_ADMIN,
        ROLE_ADMIN,
        ROLE_TEACHER,
        ROLE_STUDENT,
        ROLE_PARENT,
    )

    def post(self, request):
        question = request.data.get("question")
        return Response(
            {
                "answer": (
                    f"Hibou a bien reçu votre question : '{question}'. "
                    "Bientôt, je pourrai vous répondre avec une précision totale sur vos cours."
                )
            },
            status=status.HTTP_200_OK,
        )
