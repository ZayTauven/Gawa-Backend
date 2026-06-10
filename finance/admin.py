from django.contrib import admin
from .models import Invoice, Payment, BroadcastMessage

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'due_date', 'status')
    list_filter = ('status', 'due_date')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount_paid', 'payment_method', 'created_at')
    list_filter = ('payment_method', 'created_at')

@admin.register(BroadcastMessage)
class BroadcastMessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_audience', 'sent_by', 'created_at')
    list_filter = ('target_audience', 'created_at')
