from django.contrib import admin
from .models import Appointment, QueueEntry

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['date', 'time', 'patient', 'appointment_type', 'status']
    list_filter = ['status', 'appointment_type', 'date']
    search_fields = ['patient__full_name']

@admin.register(QueueEntry)
class QueueEntryAdmin(admin.ModelAdmin):
    list_display = ['queue_date', 'queue_number', 'patient', 'status']
    list_filter = ['status', 'queue_date']
