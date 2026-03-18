from django.contrib import admin
from .models import Patient, EmergencyContact, PregnancyHistory

class EmergencyContactInline(admin.TabularInline):
    model = EmergencyContact
    extra = 1

class PregnancyHistoryInline(admin.TabularInline):
    model = PregnancyHistory
    extra = 0

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['record_number', 'full_name', 'age', 'risk_level', 'gravida', 'para', 'contact_number', 'is_active']
    list_filter = ['risk_level', 'civil_status', 'blood_type', 'is_active']
    search_fields = ['full_name', 'record_number', 'contact_number']
    inlines = [EmergencyContactInline, PregnancyHistoryInline]
