from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient

PAYMENT_STATUS = [('unpaid','Unpaid'),('partial','Partial'),('paid','Paid'),('waived','Waived')]
PAYMENT_METHODS = [('cash','Cash'),('gcash','GCash'),('bank_transfer','Bank Transfer'),('philhealth','PhilHealth'),('other','Other')]

class Bill(models.Model):
    bill_number = models.CharField(max_length=30, unique=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bills')
    delivery_record = models.ForeignKey('delivery.DeliveryRecord', on_delete=models.SET_NULL, null=True, blank=True)
    prenatal_visit = models.ForeignKey('prenatal.PrenatalVisit', on_delete=models.SET_NULL, null=True, blank=True)
    billing_date = models.DateField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_reason = models.CharField(max_length=200, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='unpaid')
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.bill_number:
            from datetime import date
            year = date.today().year
            count = Bill.objects.filter(created_at__year=year).count() + 1
            self.bill_number = f"BILL-{year}-{count:05d}"
        self.balance = self.total_amount - self.amount_paid
        if self.balance <= 0:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'unpaid'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bill_number} - {self.patient.full_name}"

    def recalculate_totals(self):
        from decimal import Decimal
        items = self.bill_items.all()
        self.subtotal = sum(item.total_price for item in items)
        self.total_amount = self.subtotal - Decimal(str(self.discount))
        self.balance = self.total_amount - self.amount_paid
        self.save()


class BillItem(models.Model):
    ITEM_TYPES = [
        ('service','Service'),('medicine','Medicine'),
        ('supply','Supply'),('room','Room'),('procedure','Procedure'),('package','Package'),
    ]
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='bill_items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    description = models.CharField(max_length=300)
    inventory_item = models.ForeignKey('inventory.InventoryItem', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} x{self.quantity}"


class Payment(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True, help_text='GCash ref, bank ref, etc.')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            from datetime import date
            year = date.today().year
            count = Payment.objects.filter(payment_date__year=year).count() + 1
            self.receipt_number = f"OR-{year}-{count:05d}"
        super().save(*args, **kwargs)
        # Update bill totals
        bill = self.bill
        bill.amount_paid = sum(p.amount for p in bill.payments.all())
        bill.save()

    def __str__(self):
        return f"{self.receipt_number} - ₱{self.amount} ({self.payment_method})"


class PhilHealthClaim(models.Model):
    """Tracks PhilHealth case rate claims per delivery/service."""
    CASE_RATES = [
        ('nsd',          'NSD — Normal Spontaneous Delivery (₱6,500)'),
        ('cs',           'CS — Cesarean Section (₱19,000)'),
        ('premature',    'Premature Delivery (₱8,000)'),
        ('ectopic',      'Ectopic Pregnancy (₱10,000)'),
        ('abortion',     'Abortion/Miscarriage (₱4,000)'),
        ('newborn_care', 'Newborn Care Package (₱1,750)'),
        ('prenatal',     'Prenatal Package Z (₱2,500)'),
        ('other',        'Other / Custom'),
    ]
    STATUS_CHOICES = [
        ('pending',   'Pending Submission'),
        ('submitted', 'Submitted to PhilHealth'),
        ('approved',  'Approved'),
        ('rejected',  'Rejected'),
        ('resubmit',  'For Resubmission'),
        ('paid',      'Paid by PhilHealth'),
    ]
    patient         = models.ForeignKey('patients.Patient', on_delete=models.PROTECT, related_name='philhealth_claims')
    bill            = models.ForeignKey(Bill, on_delete=models.SET_NULL, null=True, blank=True, related_name='philhealth_claims')
    claim_number    = models.CharField(max_length=50, blank=True)
    case_rate_type  = models.CharField(max_length=30, choices=CASE_RATES)
    case_rate_amount= models.DecimalField(max_digits=10, decimal_places=2, default=0)
    member_pin      = models.CharField(max_length=20, blank=True, verbose_name='PhilHealth PIN')
    date_of_service = models.DateField()
    date_submitted  = models.DateField(null=True, blank=True)
    date_approved   = models.DateField(null=True, blank=True)
    amount_reimbursed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason= models.TextField(blank=True)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.full_name} — {self.get_case_rate_type_display()} ({self.status})"

    @property
    def patient_share(self):
        """What the patient still owes after PhilHealth pays."""
        if self.bill:
            return max(0, self.bill.total_amount - self.case_rate_amount)
        return 0
