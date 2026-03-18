from django.contrib import admin
from .models import PrenatalVisit, LabRequest, UltrasoundRecord

class LabRequestInline(admin.TabularInline):
    model = LabRequest
    extra = 0

@admin.register(PrenatalVisit)
class PrenatalVisitAdmin(admin.ModelAdmin):
    list_display = ['visit_date', 'patient', 'gestational_age_weeks', 'weight', 'risk_flag']
    list_filter = ['risk_flag', 'visit_date']
    search_fields = ['patient__full_name']
    inlines = [LabRequestInline]

@admin.register(UltrasoundRecord)
class UltrasoundAdmin(admin.ModelAdmin):
    list_display = ['date', 'patient', 'ga_by_ultrasound']
