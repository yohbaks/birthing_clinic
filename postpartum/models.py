from django.db import models
from django.contrib.auth.models import User


class PostpartumVisit(models.Model):
    VISIT_TYPES = [
        ('24hr',   '24-hour check (Day 1)'),
        ('3day',   '3-day check'),
        ('7day',   '1-week check (Day 7)'),
        ('6week',  '6-week postpartum'),
        ('other',  'Other / Follow-up'),
    ]
    BREASTFEEDING = [
        ('exclusive',  'Exclusive Breastfeeding'),
        ('mixed',      'Mixed (BF + formula)'),
        ('formula',    'Formula only'),
        ('none',       'Not breastfeeding'),
    ]
    FP_METHODS = [
        ('none',        'No method yet'),
        ('lam',         'LAM (Lactational Amenorrhea)'),
        ('pills',       'Combined Oral Pills'),
        ('minipill',    'Progestin-only Pill'),
        ('injectable',  'Injectable (DMPA)'),
        ('condom',      'Condom'),
        ('iud',         'IUD / IUS'),
        ('implant',     'Implant'),
        ('btl',         'BTL / Bilateral Tubal Ligation'),
        ('nfp',         'NFP / Natural Family Planning'),
        ('other',       'Other'),
    ]

    patient         = models.ForeignKey('patients.Patient', on_delete=models.PROTECT,
                                         related_name='postpartum_visits')
    delivery_record = models.ForeignKey('delivery.DeliveryRecord', on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='postpartum_visits')
    visit_date      = models.DateField()
    visit_type      = models.CharField(max_length=10, choices=VISIT_TYPES, default='6week')
    days_postpartum = models.IntegerField(null=True, blank=True)

    # Vitals
    blood_pressure_systolic  = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    temperature              = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    weight                   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pulse                    = models.IntegerField(null=True, blank=True)

    # Assessment
    uterine_involution  = models.CharField(max_length=200, blank=True,
                            help_text='e.g. Well-involuted, at umbilicus, not palpable')
    lochia              = models.CharField(max_length=200, blank=True,
                            help_text='Color, amount, odor — rubra/serosa/alba')
    wound_status        = models.CharField(max_length=200, blank=True,
                            help_text='Episiotomy/CS wound condition')
    breast_condition    = models.CharField(max_length=200, blank=True,
                            help_text='Engorgement, cracking, mastitis signs')
    breastfeeding       = models.CharField(max_length=20, choices=BREASTFEEDING, default='exclusive')
    perineum_status     = models.CharField(max_length=200, blank=True)

    # Mental health screening (Edinburgh Postnatal Depression Scale simplified)
    mood_score          = models.IntegerField(null=True, blank=True,
                            help_text='EPDS total score (0-30). ≥10 = possible depression')
    mood_notes          = models.TextField(blank=True,
                            help_text='Notes on emotional/mental health status')

    # Family planning
    fp_counseled        = models.BooleanField(default=False)
    fp_method_chosen    = models.CharField(max_length=20, choices=FP_METHODS, default='none')
    fp_method_provided  = models.BooleanField(default=False)

    # Newborn check
    newborn_weight      = models.IntegerField(null=True, blank=True, help_text='grams')
    newborn_condition   = models.CharField(max_length=200, blank=True)
    newborn_feeding     = models.CharField(max_length=200, blank=True)

    # Plan
    chief_complaint     = models.TextField(blank=True)
    assessment          = models.TextField(blank=True)
    plan                = models.TextField(blank=True)
    prescribed_medicines= models.TextField(blank=True)
    referral            = models.CharField(max_length=200, blank=True)
    follow_up_date      = models.DateField(null=True, blank=True)
    notes               = models.TextField(blank=True)

    attending_staff     = models.ForeignKey(User, on_delete=models.SET_NULL,
                                             null=True, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date']

    def __str__(self):
        return f"{self.patient.full_name} — {self.get_visit_type_display()} on {self.visit_date}"

    @property
    def bp_display(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return "—"

    @property
    def is_depression_risk(self):
        return self.mood_score is not None and self.mood_score >= 10
