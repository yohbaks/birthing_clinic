from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient

DELIVERY_TYPES = [
    ('nsd','Normal Spontaneous Delivery'),
    ('assisted','Assisted Delivery'),
    ('cs','Cesarean Section'),
    ('referral','Referral'),
]
PRESENTATION_CHOICES = [
    ('cephalic','Cephalic'),('breech','Breech'),
    ('transverse','Transverse'),('other','Other'),
]

class DeliveryRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='deliveries')
    admission_datetime = models.DateTimeField()
    chief_complaint = models.TextField(blank=True)
    attending_midwife = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries_midwife'
    )
    attending_doctor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries_doctor'
    )
    labor_start_time = models.DateTimeField(null=True, blank=True)
    full_dilation_time = models.DateTimeField(null=True, blank=True)
    delivery_datetime = models.DateTimeField(null=True, blank=True)
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPES, blank=True)
    presentation = models.CharField(max_length=20, choices=PRESENTATION_CHOICES, blank=True)
    placenta_delivery_time = models.DateTimeField(null=True, blank=True)
    estimated_blood_loss = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True, help_text='mL')
    complications = models.TextField(blank=True)
    maternal_condition = models.TextField(blank=True)
    referral_hospital = models.CharField(max_length=200, blank=True)
    referral_reason = models.TextField(blank=True)
    discharge_datetime = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-admission_datetime']

    def __str__(self):
        return f"{self.patient.full_name} - {self.admission_datetime.date()}"

    @property
    def labor_duration(self):
        if self.labor_start_time and self.delivery_datetime:
            return self.delivery_datetime - self.labor_start_time
        return None


class LaborMonitoring(models.Model):
    MEMBRANE_STATUS = [('intact','Intact'),('ruptured','Ruptured'),('artificial','Artificially Ruptured')]
    delivery_record = models.ForeignKey(DeliveryRecord, on_delete=models.CASCADE, related_name='labor_monitoring')
    recorded_at = models.DateTimeField()
    contraction_frequency = models.CharField(max_length=100, blank=True, help_text='e.g. 3 in 10 min')
    contraction_duration = models.CharField(max_length=100, blank=True, help_text='seconds')
    fetal_heart_rate = models.PositiveIntegerField(null=True, blank=True, help_text='bpm')
    cervical_dilation = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, help_text='cm')
    maternal_bp_systolic = models.PositiveIntegerField(null=True, blank=True)
    maternal_bp_diastolic = models.PositiveIntegerField(null=True, blank=True)
    maternal_pulse = models.PositiveIntegerField(null=True, blank=True)
    membrane_status = models.CharField(max_length=20, choices=MEMBRANE_STATUS, default='intact')
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['recorded_at']


class DeliveryComplication(models.Model):
    delivery_record = models.ForeignKey(DeliveryRecord, on_delete=models.CASCADE, related_name='complication_records')
    complication_type = models.CharField(max_length=200)
    description = models.TextField()
    action_taken = models.TextField()
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
