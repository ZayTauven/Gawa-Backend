"""
URL configuration for gawa_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import EmailOrUsernameTokenObtainPairView
from exam.views import HibouGenerateQuizView, StudentQuizSubmitView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication
    path('api/v1/auth/token/', EmailOrUsernameTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/users/', include('users.urls')),

    
    # Feature Modules
    path('api/v1/sis/', include('sis.urls')),
    path('api/v1/pcs/', include('pcs.urls')),
    path('api/v1/exam/', include('exam.urls')),
    path('api/v1/ai/generate-quiz', HibouGenerateQuizView.as_view(), name='ai-generate-quiz'),
    path('api/v1/student/quiz/<uuid:quiz_id>/submit', StudentQuizSubmitView.as_view(), name='student-quiz-submit'),
    path('api/v1/finance/', include('finance.urls')),
    path('api/v1/vault/', include('vault.urls')),
]
