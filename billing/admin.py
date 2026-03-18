from django.contrib import admin
from .models import Bill, BillItem, Payment

class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['receipt_number']

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['bill_number', 'patient', 'billing_date', 'total_amount', 'amount_paid', 'balance', 'payment_status']
    list_filter = ['payment_status']
    search_fields = ['bill_number', 'patient__full_name']
    inlines = [BillItemInline, PaymentInline]
    readonly_fields = ['bill_number', 'subtotal', 'total_amount', 'balance', 'payment_status']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'bill', 'amount', 'payment_method', 'payment_date']
    readonly_fields = ['receipt_number']
