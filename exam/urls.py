from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChoiceViewSet,
    HibouAskView,
    HibouCreateApprovedQuizView,
    HibouGenerateQuizView,
    QuestionViewSet,
    QuizViewSet,
    StudentAttemptViewSet,
)

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'choices', ChoiceViewSet, basename='choice')
router.register(r'attempts', StudentAttemptViewSet, basename='attempt')

urlpatterns = [
    path('', include(router.urls)),
    path('hibou/generate-quiz/', HibouGenerateQuizView.as_view(), name='hibou-generate-quiz'),
    path('hibou/create-approved-quiz/', HibouCreateApprovedQuizView.as_view(), name='hibou-create-approved-quiz'),
    path('hibou/ask/', HibouAskView.as_view(), name='hibou-ask'),
]
