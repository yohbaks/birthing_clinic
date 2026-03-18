from django.db import models
from django.utils import timezone

class InventoryCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Inventory Categories'

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    UNIT_CHOICES = [
        ('pc','Piece'),('box','Box'),('vial','Vial'),('ampule','Ampule'),
        ('tablet','Tablet'),('capsule','Capsule'),('ml','mL'),('liter','Liter'),
        ('set','Set'),('pair','Pair'),('pack','Pack'),('roll','Roll'),('bottle','Bottle'),
    ]
    item_code = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(InventoryCategory, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='pc')
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_stock_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.item_code:
            count = InventoryItem.objects.count() + 1
            self.item_code = f"ITEM-{count:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_code} - {self.name}"

    @property
    def is_low_stock(self):
        return self.quantity_on_hand <= self.reorder_level

    @property
    def is_out_of_stock(self):
        return self.quantity_on_hand <= 0


class StockBatch(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    received_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    is_expired = models.BooleanField(default=False)

    class Meta:
        ordering = ['expiry_date']

    def __str__(self):
        return f"{self.item.name} - Batch {self.batch_number} (Exp: {self.expiry_date})"

    @property
    def is_near_expiry(self):
        if self.expiry_date:
            from datetime import date, timedelta
            return self.expiry_date <= date.today() + timedelta(days=90)
        return False


class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('stock_in','Stock In'),('stock_out','Stock Out'),
        ('adjustment','Adjustment'),('expired','Expired'),
        ('damaged','Damaged'),('return','Return'),
    ]
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    batch = models.ForeignKey(StockBatch, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=200, blank=True, help_text='Patient record, PO number, etc.')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.item.name} {self.transaction_type} {self.quantity} ({self.created_at.date()})"


class PurchaseOrder(models.Model):
    PO_STATUS = [('draft','Draft'),('ordered','Ordered'),('received','Received'),('cancelled','Cancelled')]
    po_number = models.CharField(max_length=50, unique=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    order_date = models.DateField(default=timezone.now)
    expected_delivery = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PO_STATUS, default='draft')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.po_number:
            from datetime import date
            year = date.today().year
            count = PurchaseOrder.objects.filter(created_at__year=year).count() + 1
            self.po_number = f"PO-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.po_number} - {self.supplier}"


class PurchaseItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)

    @property
    def total_cost(self):
        return self.quantity_ordered * self.unit_cost
