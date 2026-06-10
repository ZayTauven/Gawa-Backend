from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SchoolMembershipViewSet, SchoolViewSet, UserViewSet

router = DefaultRouter()
router.register(r'schools', SchoolViewSet, basename='school')
router.register(r'school-memberships', SchoolMembershipViewSet, basename='school-membership')
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
