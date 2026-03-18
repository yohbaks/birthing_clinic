from django.db import models
from django.contrib.auth.models import User

ROLES = [
    ('super_admin','Super Admin'),('admin','Administrator'),
    ('doctor','Doctor'),('midwife','Midwife'),('nurse','Nurse'),
    ('cashier','Cashier'),('receptionist','Receptionist'),
    ('inventory_clerk','Inventory Clerk'),
]

class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    role = models.CharField(max_length=30, choices=ROLES)
    employee_id = models.CharField(max_length=30, unique=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    profile_photo = models.ImageField(upload_to='staff_photos/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            count = StaffProfile.objects.count() + 1
            self.employee_id = f"EMP-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def can_manage_patients(self):
        return self.role in ['super_admin','admin','doctor','midwife','nurse','receptionist']

    @property
    def can_manage_billing(self):
        return self.role in ['super_admin','admin','cashier']

    @property
    def can_manage_inventory(self):
        return self.role in ['super_admin','admin','inventory_clerk']


class ClinicSettings(models.Model):
    """Singleton model for clinic configuration."""
    clinic_name        = models.CharField(max_length=200, default='BirthCare Clinic')
    clinic_tagline     = models.CharField(max_length=200, default='Maternity & Newborn Care Services', blank=True)
    address            = models.TextField(blank=True)
    contact_number     = models.CharField(max_length=50, blank=True)
    email              = models.EmailField(blank=True)
    philhealth_accno   = models.CharField(max_length=50, blank=True, verbose_name='PhilHealth Accreditation No.')
    doh_license        = models.CharField(max_length=50, blank=True, verbose_name='DOH License No.')
    head_physician     = models.CharField(max_length=200, blank=True)
    head_midwife       = models.CharField(max_length=200, blank=True)
    default_delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    default_room_rate  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    logo_url           = models.CharField(max_length=500, blank=True, default='🌸')
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Clinic Settings"

    def __str__(self):
        return self.clinic_name

    @classmethod
    def get(cls):
        """Get or create the singleton settings instance."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class LoginAttempt(models.Model):
    """Tracks failed login attempts for brute-force protection."""
    ip_address  = models.GenericIPAddressField()
    username    = models.CharField(max_length=150, blank=True)
    attempted_at= models.DateTimeField(auto_now_add=True)
    success     = models.BooleanField(default=False)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.username} from {self.ip_address} at {self.attempted_at}"


class ActiveSession(models.Model):
    """Tracks currently active user sessions."""
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.username} — {self.ip_address}"
