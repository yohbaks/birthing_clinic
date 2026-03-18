from django.db import models
from patients.models import Patient
from delivery.models import DeliveryRecord

GENDER_CHOICES = [('male','Male'),('female','Female'),('indeterminate','Indeterminate')]
BIRTH_STATUS = [('alive','Alive'),('stillbirth','Stillbirth'),('neonatal_death','Neonatal Death')]

class NewbornRecord(models.Model):
    mother = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='newborns')
    delivery_record = models.ForeignKey(DeliveryRecord, on_delete=models.CASCADE, related_name='newborns')
    baby_name = models.CharField(max_length=200, blank=True)
    baby_id = models.CharField(max_length=20, unique=True, blank=True)
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES)
    birth_datetime = models.DateTimeField()
    weight_grams = models.DecimalField(max_digits=6, decimal_places=0, help_text='grams')
    length_cm = models.DecimalField(max_digits=4, decimal_places=1, help_text='cm')
    head_circumference_cm = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    chest_circumference_cm = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    apgar_1min = models.PositiveIntegerField(null=True, blank=True)
    apgar_5min = models.PositiveIntegerField(null=True, blank=True)
    birth_status = models.CharField(max_length=20, choices=BIRTH_STATUS, default='alive')
    initial_diagnosis = models.TextField(blank=True)
    vitamin_k_given = models.BooleanField(default=False)
    eye_prophylaxis_given = models.BooleanField(default=False)
    newborn_screening_done = models.BooleanField(default=False)
    newborn_screening_date = models.DateField(null=True, blank=True)
    discharge_datetime = models.DateTimeField(null=True, blank=True)
    discharge_weight_grams = models.DecimalField(max_digits=6, decimal_places=0, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.baby_id:
            from datetime import date
            year = date.today().year
            count = NewbornRecord.objects.filter(created_at__year=year).count() + 1
            self.baby_id = f"NB-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.baby_name or 'Baby'
        return f"{name} ({self.baby_id}) - Mother: {self.mother.full_name}"

    @property
    def weight_kg(self):
        return round(float(self.weight_grams) / 1000, 3)


class NewbornImmunization(models.Model):
    newborn = models.ForeignKey(NewbornRecord, on_delete=models.CASCADE, related_name='immunizations')
    vaccine_name = models.CharField(max_length=200)
    date_given = models.DateField()
    dose = models.CharField(max_length=100, blank=True)
    administered_by = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.vaccine_name} - {self.newborn.baby_id}"
