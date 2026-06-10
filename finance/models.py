import uuid
from django.db import models
from django.conf import settings
from sis.models import Student

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partial'),
        ('OVERDUE', 'Overdue'),
        ('PENDING', 'Pending'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    invoice_period = models.CharField(max_length=50)

    def __str__(self):
        return f"Invoice {self.invoice_period} - {self.student.matricule}"

class Payment(models.Model):
    METHOD_CHOICES = (
        ('CASH', 'Cash'),
        ('CHECK', 'Check'),
        ('MOBILE_MONEY', 'Mobile Money'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    receipt_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount_paid} for {self.invoice.id}"

class BroadcastMessage(models.Model):
    AUDIENCE_CHOICES = (
        ('ALL', 'All'),
        ('SPECIFIC_CLASSROOMS', 'Specific Classrooms'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey('users.School', on_delete=models.CASCADE, related_name='broadcast_messages', null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    target_audience = models.CharField(max_length=30, choices=AUDIENCE_CHOICES, default='ALL')
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
