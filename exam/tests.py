from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from exam.models import Choice, Question, Quiz, StudentAttempt
from pcs.models import Chapter, Course, Resource
from sis.models import Student
from users.models import School


class ExamApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.school = School.objects.create(code="SCH-EXAM", name="School Exam")
        self.teacher = user_model.objects.create_user(
            username="teachgrade",
            email="teachgrade@example.com",
            password="StrongPass123!",
            role="TEACHER",
            default_school=self.school,
        )
        self.parent = user_model.objects.create_user(
            username="parentgrade",
            email="parentgrade@example.com",
            password="StrongPass123!",
            role="PARENT",
            default_school=self.school,
        )
        self.student_user = user_model.objects.create_user(
            username="studentgrade",
            email="studentgrade@example.com",
            password="StrongPass123!",
            role="STUDENT",
            default_school=self.school,
        )
        self.other_student_user = user_model.objects.create_user(
            username="studentother",
            email="studentother@example.com",
            password="StrongPass123!",
            role="STUDENT",
            default_school=self.school,
        )
        self.student = Student.objects.create(
            user=self.student_user,
            school=self.school,
            parent_user=self.parent,
            matricule="MAT-EXAM-001",
        )
        self.other_student = Student.objects.create(
            user=self.other_student_user,
            school=self.school,
            matricule="MAT-EXAM-002",
        )

        self.course = Course.objects.create(
            teacher=self.teacher,
            title="Physique",
            description="Cours physique",
        )
        self.chapter = Chapter.objects.create(
            course=self.course,
            title="Chapitre 1",
            order=1,
            status="UNLOCKED",
        )
        self.quiz = Quiz.objects.create(
            chapter=self.chapter,
            title="Quiz Forces",
            status="PUBLISHED",
        )
        self.resource = Resource.objects.create(
            chapter=self.chapter,
            title="Forces fondamentales",
            type="TEXT",
            url="",
            status="UNLOCKED",
        )

        question = Question.objects.create(
            quiz=self.quiz,
            text="Quelle force attire les corps vers la Terre ?",
            source_reference="Physique - Forces fondamentales",
        )
        self.correct_choice = Choice.objects.create(
            question=question,
            text="La gravite",
            is_correct=True,
        )
        self.wrong_choice = Choice.objects.create(
            question=question,
            text="La friction",
            is_correct=False,
        )

    def test_student_cannot_create_attempt_for_other_student(self):
        self.client.force_authenticate(user=self.student_user)
        payload = {
            "student": str(self.other_student.id),
            "quiz": str(self.quiz.id),
            "score": 77,
        }

        response = self.client.post("/api/v1/exam/attempts/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_parent_sees_only_child_attempts(self):
        StudentAttempt.objects.create(student=self.student, quiz=self.quiz, score=91)
        StudentAttempt.objects.create(student=self.other_student, quiz=self.quiz, score=35)

        self.client.force_authenticate(user=self.parent)
        response = self.client.get("/api/v1/exam/attempts/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(str(response.data[0]["student"]), str(self.student.id))

    def test_teacher_can_generate_hibou_quiz_draft_payload(self):
        self.client.force_authenticate(user=self.teacher)
        payload = {
            "resource_id": str(self.resource.id),
            "number_of_questions": 4,
            "difficulty": "MEDIUM",
        }
        response = self.client.post("/api/v1/ai/generate-quiz", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["questions"]), 4)
        self.assertEqual(response.data["chapter_id"], str(self.chapter.id))

    def test_teacher_can_create_approved_quiz(self):
        self.client.force_authenticate(user=self.teacher)
        payload = {
            "chapter_id": str(self.chapter.id),
            "title": "Quiz revise Forces",
            "status": "PUBLISHED",
            "questions": [
                {
                    "text": "Quel terme decrit l'attraction terrestre ?",
                    "source_reference": "Physique - Forces fondamentales",
                    "choices": [
                        {"text": "Gravite", "is_correct": True},
                        {"text": "Inertie", "is_correct": False},
                        {"text": "Vitesse", "is_correct": False},
                    ],
                }
            ],
        }
        response = self.client.post("/api/v1/exam/hibou/create-approved-quiz/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "PUBLISHED")
        self.assertEqual(Quiz.objects.filter(title="Quiz revise Forces").count(), 1)

    def test_student_can_submit_quiz_and_server_computes_score(self):
        self.client.force_authenticate(user=self.student_user)
        payload = {
            "answers": [
                {
                    "question_id": str(self.correct_choice.question_id),
                    "choice_id": str(self.correct_choice.id),
                }
            ]
        }
        response = self.client.post(
            f"/api/v1/student/quiz/{self.quiz.id}/submit",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["score"], 100)
        self.assertEqual(StudentAttempt.objects.filter(student=self.student, quiz=self.quiz).count(), 1)

    def test_student_cannot_submit_draft_quiz(self):
        draft_quiz = Quiz.objects.create(
            chapter=self.chapter,
            title="Quiz Brouillon",
            status="DRAFT",
        )
        question = Question.objects.create(quiz=draft_quiz, text="Question draft")
        choice = Choice.objects.create(question=question, text="Option", is_correct=True)

        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(
            f"/api/v1/student/quiz/{draft_quiz.id}/submit",
            {"answers": [{"question_id": str(question.id), "choice_id": str(choice.id)}]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
