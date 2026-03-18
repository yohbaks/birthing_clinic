from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient

class PrenatalVisit(models.Model):
    RISK_FLAGS = [('normal','Normal'),('borderline','Borderline'),('high_risk','High Risk')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prenatal_visits')
    visit_date = models.DateField()
    gestational_age_weeks = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text='kg')
    blood_pressure_systolic = models.PositiveIntegerField()
    blood_pressure_diastolic = models.PositiveIntegerField()
    temperature = models.DecimalField(max_digits=4, decimal_places=1, help_text='°C')
    fetal_heart_rate = models.PositiveIntegerField(null=True, blank=True, help_text='bpm')
    fundal_height = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text='cm')
    chief_complaint = models.TextField(blank=True)
    assessment = models.TextField()
    plan = models.TextField()
    prescribed_medicines = models.TextField(blank=True)
    lab_request = models.TextField(blank=True)
    ultrasound_request = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    attending_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    risk_flag = models.CharField(max_length=20, choices=RISK_FLAGS, default='normal')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visit_date']

    def __str__(self):
        return f"{self.patient.full_name} - {self.visit_date} (GA: {self.gestational_age_weeks}w)"

    @property
    def bp_display(self):
        return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"

    @property
    def is_bp_high(self):
        return self.blood_pressure_systolic >= 140 or self.blood_pressure_diastolic >= 90


class LabRequest(models.Model):
    visit = models.ForeignKey(PrenatalVisit, on_delete=models.CASCADE, related_name='lab_requests')
    test_name = models.CharField(max_length=200)
    result = models.TextField(blank=True)
    result_date = models.DateField(null=True, blank=True)
    result_file = models.FileField(upload_to='lab_results/', null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.test_name} - {self.visit.patient.full_name}"


class UltrasoundRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='ultrasounds')
    visit = models.ForeignKey(PrenatalVisit, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    findings = models.TextField()
    ga_by_ultrasound = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    image_file = models.FileField(upload_to='ultrasounds/', null=True, blank=True)
    done_by = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
