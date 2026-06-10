from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SealedArchiveViewSet, ArchiveAccessLogViewSet

router = DefaultRouter()
router.register(r'archives', SealedArchiveViewSet, basename='archive')
router.register(r'access-logs', ArchiveAccessLogViewSet, basename='access-log')

urlpatterns = [
    path('', include(router.urls)),
]
