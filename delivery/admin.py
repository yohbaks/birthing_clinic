from django.contrib import admin
from .models import DeliveryRecord, LaborMonitoring, DeliveryComplication

class LaborMonitoringInline(admin.TabularInline):
    model = LaborMonitoring
    extra = 0

@admin.register(DeliveryRecord)
class DeliveryRecordAdmin(admin.ModelAdmin):
    list_display = ['admission_datetime', 'patient', 'delivery_type', 'delivery_datetime']
    list_filter = ['delivery_type']
    search_fields = ['patient__full_name']
    inlines = [LaborMonitoringInline]
