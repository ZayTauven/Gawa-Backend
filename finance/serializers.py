from rest_framework import serializers
from .models import Invoice, Payment, BroadcastMessage

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'student', 'amount', 'due_date', 'status', 'invoice_period']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'invoice', 'amount_paid', 'payment_method', 'recorded_by', 'receipt_url', 'created_at']
        read_only_fields = ['recorded_by', 'created_at']

class BroadcastMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BroadcastMessage
        fields = ['id', 'school', 'title', 'content', 'target_audience', 'sent_by', 'created_at']
        read_only_fields = ['school', 'sent_by', 'created_at']
