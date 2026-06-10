from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, ClassroomViewSet, AttendanceViewSet, SyncAttendanceView, LiaisonNoteViewSet, WatermelonSyncView, TimetableSlotViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'classrooms', ClassroomViewSet)
router.register(r'attendance-records', AttendanceViewSet)
router.register(r'timetable-slots', TimetableSlotViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('attendance/sync/', SyncAttendanceView.as_view(), name='sync-attendance'),
    path('sync/watermelon/', WatermelonSyncView.as_view(), name='watermelon-sync'),
    path('students/<str:student_pk>/carnet/', LiaisonNoteViewSet.as_view({'get': 'list'}), name='student-carnet'),
]
