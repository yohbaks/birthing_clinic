from django.db import models
from django.utils import timezone
import uuid

BLOOD_TYPES = [('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-')]
CIVIL_STATUS = [('single','Single'),('married','Married'),('widowed','Widowed'),('separated','Separated'),('live_in','Live-in')]
RISK_LEVELS = [('low','Low Risk'),('high','High Risk'),('moderate','Moderate Risk')]

class Patient(models.Model):
    record_number = models.CharField(max_length=20, unique=True, blank=True)
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS, default='single')
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    partner_name = models.CharField(max_length=200, blank=True)
    blood_type = models.CharField(max_length=5, choices=BLOOD_TYPES, blank=True)
    allergies = models.TextField(blank=True)
    existing_conditions = models.TextField(blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='low')
    gravida = models.PositiveIntegerField(default=0, help_text='Total pregnancies')
    para = models.PositiveIntegerField(default=0, help_text='Total deliveries')
    abortion_history = models.PositiveIntegerField(default=0)
    lmp = models.DateField(null=True, blank=True, verbose_name='Last Menstrual Period')
    edd = models.DateField(null=True, blank=True, verbose_name='Expected Date of Delivery')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.record_number} - {self.full_name}"

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def save(self, *args, **kwargs):
        if not self.record_number:
            from datetime import date
            year = date.today().year
            count = Patient.objects.filter(created_at__year=year).count() + 1
            self.record_number = f"PAT-{year}-{count:04d}"
        super().save(*args, **kwargs)


class EmergencyContact(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.patient.full_name}"


class PregnancyHistory(models.Model):
    OUTCOME_CHOICES = [
        ('live_birth','Live Birth'),('stillbirth','Stillbirth'),
        ('abortion','Abortion'),('ectopic','Ectopic'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='pregnancy_history')
    year = models.PositiveIntegerField()
    delivery_type = models.CharField(max_length=100, blank=True)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES)
    birth_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    complications = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-year']


class MaternalImmunization(models.Model):
    """Tracks maternal vaccines (tetanus toxoid, flu, etc.)."""
    VACCINE_CHOICES = [
        ('tt1',  'Tetanus Toxoid 1 (TT1)'),
        ('tt2',  'Tetanus Toxoid 2 (TT2)'),
        ('tt3',  'Tetanus Toxoid 3 (TT3)'),
        ('tt4',  'Tetanus Toxoid 4 (TT4)'),
        ('tt5',  'Tetanus Toxoid 5 (TT5)'),
        ('flu',  'Influenza'),
        ('hepb', 'Hepatitis B'),
        ('covid','COVID-19'),
        ('other','Other'),
    ]
    patient     = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='maternal_immunizations')
    vaccine     = models.CharField(max_length=20, choices=VACCINE_CHOICES)
    date_given  = models.DateField()
    given_by    = models.CharField(max_length=200, blank=True)
    facility    = models.CharField(max_length=200, blank=True)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_given']

    def __str__(self):
        return f"{self.patient.full_name} — {self.get_vaccine_display()} on {self.date_given}"
