from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, PaymentViewSet, BroadcastMessageViewSet

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'broadcast-messages', BroadcastMessageViewSet, basename='broadcastmessage')

urlpatterns = [
    path('', include(router.urls)),
]
