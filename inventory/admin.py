from django.contrib import admin
from .models import InventoryCategory, Supplier, InventoryItem, StockBatch, StockTransaction, PurchaseOrder, PurchaseItem

@admin.register(InventoryCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'is_active']

class StockBatchInline(admin.TabularInline):
    model = StockBatch
    extra = 0

@admin.register(InventoryItem)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['item_code', 'name', 'category', 'unit', 'quantity_on_hand', 'reorder_level', 'selling_price', 'is_active']
    list_filter = ['category', 'unit', 'is_active']
    search_fields = ['name', 'item_code']
    inlines = [StockBatchInline]

@admin.register(StockTransaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'item', 'transaction_type', 'quantity', 'balance_after']
    list_filter = ['transaction_type']

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1

@admin.register(PurchaseOrder)
class POAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'supplier', 'order_date', 'status', 'total_amount']
    inlines = [PurchaseItemInline]
