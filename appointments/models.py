from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient

APPT_STATUS = [
    ('pending','Pending'),('confirmed','Confirmed'),('completed','Completed'),
    ('cancelled','Cancelled'),('no_show','No Show'),
]
APPT_TYPES = [
    ('prenatal','Prenatal Checkup'),('postpartum','Postpartum'),
    ('consultation','Consultation'),('lab','Lab Work'),
    ('ultrasound','Ultrasound'),('follow_up','Follow-up'),('walk_in','Walk-in'),
]

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    appointment_type = models.CharField(max_length=20, choices=APPT_TYPES)
    assigned_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=APPT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.patient.full_name} - {self.date} {self.time}"


class QueueEntry(models.Model):
    QUEUE_STATUS = [('waiting','Waiting'),('in_progress','In Progress'),('done','Done'),('skipped','Skipped')]
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='queue_entry', null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    queue_date = models.DateField()
    queue_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=QUEUE_STATUS, default='waiting')
    called_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['queue_date', 'queue_number']
        unique_together = ['queue_date', 'queue_number']

    def __str__(self):
        return f"Queue #{self.queue_number} - {self.patient.full_name} ({self.queue_date})"
