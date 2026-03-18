from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from accounts.permissions import role_required
from decimal import Decimal
from .models import (InventoryItem, InventoryCategory, StockBatch,
                     StockTransaction, PurchaseOrder, PurchaseItem, Supplier)

@login_required
@role_required('inventory')
def inventory_list(request):
    q = request.GET.get('q', '')
    cat_filter = request.GET.get('category', '')
    items = InventoryItem.objects.select_related('category').filter(is_active=True)
    if q:
        items = items.filter(name__icontains=q)
    if cat_filter:
        items = items.filter(category_id=cat_filter)
    categories = InventoryCategory.objects.all()
    return render(request, 'inventory/inventory_list.html', {
        'items': items, 'categories': categories,
        'query': q, 'cat_filter': cat_filter,
    })

@login_required
@role_required('inventory')
def item_add(request):
    categories = InventoryCategory.objects.all()
    suppliers = Supplier.objects.filter(is_active=True)
    if request.method == 'POST':
        p = request.POST
        item = InventoryItem.objects.create(
            name=p.get('name'),
            category_id=p.get('category') or None,
            description=p.get('description', ''),
            unit=p.get('unit', 'pc'),
            minimum_stock_level=p.get('min_stock', 0),
            reorder_level=p.get('reorder_level', 0),
            cost_price=p.get('cost_price', 0),
            selling_price=p.get('selling_price', 0),
        )
        messages.success(request, f'Item {item.name} added. Code: {item.item_code}')
        return redirect('item_detail', pk=item.pk)
    return render(request, 'inventory/item_form.html', {'categories': categories, 'suppliers': suppliers})

@login_required
@role_required('inventory')
def item_detail(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    transactions = item.transactions.all().order_by('-created_at')[:30]
    batches = item.batches.all().order_by('expiry_date')
    return render(request, 'inventory/item_detail.html', {
        'item': item, 'transactions': transactions, 'batches': batches
    })

@login_required
@role_required('inventory')
def item_edit(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    categories = InventoryCategory.objects.all()
    if request.method == 'POST':
        p = request.POST
        item.name = p.get('name', item.name)
        item.category_id = p.get('category') or item.category_id
        item.description = p.get('description', item.description)
        item.unit = p.get('unit', item.unit)
        item.minimum_stock_level = p.get('min_stock', item.minimum_stock_level)
        item.reorder_level = p.get('reorder_level', item.reorder_level)
        item.cost_price = p.get('cost_price', item.cost_price)
        item.selling_price = p.get('selling_price', item.selling_price)
        item.save()
        messages.success(request, 'Item updated.')
        return redirect('item_detail', pk=pk)
    return render(request, 'inventory/item_form.html', {'item': item, 'categories': categories})

@login_required
@role_required('inventory')
def stock_in(request):
    items = InventoryItem.objects.filter(is_active=True).order_by('name')
    if request.method == 'POST':
        p = request.POST
        item = get_object_or_404(InventoryItem, pk=p.get('item'))
        qty = Decimal(str(p.get('quantity', 0) or 0))
        if qty <= 0:
            messages.error(request, 'Quantity must be positive.')
            return redirect('stock_in')
        item.quantity_on_hand = item.quantity_on_hand + qty
        item.save()
        StockTransaction.objects.create(
            item=item, transaction_type='stock_in', quantity=qty,
            balance_after=item.quantity_on_hand,
            reference=p.get('reference', ''),
            notes=p.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, f'Stock in: {qty} {item.get_unit_display()} of {item.name}. New balance: {item.quantity_on_hand}')
        return redirect('inventory_list')
    return render(request, 'inventory/stock_in.html', {'items': items})

@login_required
@role_required('inventory')
def stock_out(request):
    items = InventoryItem.objects.filter(is_active=True).order_by('name')
    if request.method == 'POST':
        p = request.POST
        item = get_object_or_404(InventoryItem, pk=p.get('item'))
        qty = Decimal(str(p.get('quantity', 0) or 0))
        if qty > item.quantity_on_hand:
            messages.error(request, f'Insufficient stock. Available: {item.quantity_on_hand} {item.get_unit_display()}')
            return redirect('stock_out')
        item.quantity_on_hand = item.quantity_on_hand - qty
        item.save()
        StockTransaction.objects.create(
            item=item, transaction_type='stock_out', quantity=qty,
            balance_after=item.quantity_on_hand,
            reference=p.get('reference', ''),
            notes=p.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, f'Stock out: {qty} {item.get_unit_display()} of {item.name}. Remaining: {item.quantity_on_hand}')
        return redirect('inventory_list')
    return render(request, 'inventory/stock_out.html', {'items': items})

@login_required
@role_required('inventory')
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

@login_required
@role_required('inventory')
def supplier_add(request):
    if request.method == 'POST':
        p = request.POST
        Supplier.objects.create(
            name=p.get('name', ''),
            contact_person=p.get('contact_person', ''),
            phone=p.get('phone', ''),
            email=p.get('email', ''),
            address=p.get('address', ''),
        )
        messages.success(request, 'Supplier added.')
        return redirect('supplier_list')
    return render(request, 'inventory/supplier_form.html')

@login_required
@role_required('inventory')
def low_stock(request):
    items = InventoryItem.objects.filter(is_active=True).extra(
        where=['quantity_on_hand <= reorder_level']
    ).order_by('quantity_on_hand')
    return render(request, 'inventory/low_stock.html', {'items': items})

@login_required
@role_required('inventory')
def expiry_report(request):
    from datetime import date, timedelta
    today = date.today()
    near_expiry = StockBatch.objects.filter(
        expiry_date__isnull=False,
        expiry_date__gt=today,
        expiry_date__lte=today + timedelta(days=90),
        is_expired=False,
    ).select_related('item').order_by('expiry_date')
    expired = StockBatch.objects.filter(
        expiry_date__isnull=False,
        expiry_date__lte=today,
    ).select_related('item').order_by('expiry_date')
    return render(request, 'inventory/expiry_report.html', {
        'near_expiry': near_expiry, 'expired': expired
    })

@login_required
@role_required('inventory')
def purchase_order_list(request):
    orders = PurchaseOrder.objects.select_related('supplier').order_by('-order_date')
    return render(request, 'inventory/po_list.html', {'orders': orders})

@login_required
@role_required('inventory')
def purchase_order_add(request):
    suppliers = Supplier.objects.filter(is_active=True)
    items = InventoryItem.objects.filter(is_active=True).order_by('name')
    if request.method == 'POST':
        p = request.POST
        supplier = get_object_or_404(Supplier, pk=p.get('supplier'))
        po = PurchaseOrder.objects.create(
            supplier=supplier,
            order_date=p.get('order_date'),
            expected_delivery=p.get('expected_delivery') or None,
            notes=p.get('notes', ''),
            created_by=request.user,
        )
        descs = request.POST.getlist('item[]')
        qtys = request.POST.getlist('qty_ordered[]')
        costs = request.POST.getlist('unit_cost[]')
        for item_id, qty, cost in zip(descs, qtys, costs):
            if item_id and qty:
                PurchaseItem.objects.create(
                    purchase_order=po,
                    inventory_item_id=item_id,
                    quantity_ordered=Decimal(str(qty or 1)),
                    unit_cost=Decimal(str(cost or 0)),
                )
        # Recalc total
        po.total_amount = sum(
            pi.quantity_ordered * pi.unit_cost for pi in po.items.all()
        )
        po.save()
        messages.success(request, f'Purchase Order {po.po_number} created.')
        return redirect('po_detail', pk=po.pk)
    return render(request, 'inventory/po_form.html', {'suppliers': suppliers, 'items': items})

@login_required
@role_required('inventory')
def purchase_order_detail(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    po_items = po.items.select_related('inventory_item').all()
    return render(request, 'inventory/po_detail.html', {'po': po, 'po_items': po_items})

@login_required
@role_required('inventory')
def receive_purchase_order(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    po_items = po.items.select_related('inventory_item').all()
    if request.method == 'POST':
        from django.utils import timezone as tz
        for po_item in po_items:
            qty_key = f'qty_received_{po_item.pk}'
            expiry_key = f'expiry_{po_item.pk}'
            batch_key = f'batch_{po_item.pk}'
            qty_received = Decimal(str(request.POST.get(qty_key, 0) or 0))
            if qty_received > 0:
                po_item.quantity_received = qty_received
                po_item.save()
                # Update stock
                item = po_item.inventory_item
                item.quantity_on_hand = item.quantity_on_hand + qty_received
                item.save()
                # Create batch record
                expiry = request.POST.get(expiry_key) or None
                batch_no = request.POST.get(batch_key, '')
                if expiry or batch_no:
                    StockBatch.objects.create(
                        item=item,
                        batch_number=batch_no,
                        expiry_date=expiry,
                        quantity=qty_received,
                        supplier=po.supplier,
                    )
                # Transaction
                StockTransaction.objects.create(
                    item=item,
                    transaction_type='stock_in',
                    quantity=qty_received,
                    balance_after=item.quantity_on_hand,
                    reference=f'PO-{po.po_number}',
                    created_by=request.user,
                )
        po.status = 'received'
        po.received_date = tz.now().date()
        po.save()
        messages.success(request, f'Purchase Order {po.po_number} received and stock updated.')
        return redirect('po_detail', pk=pk)
    return render(request, 'inventory/po_receive.html', {'po': po, 'po_items': po_items})

@login_required
@role_required('inventory')
def supplier_detail(request, pk):
    from inventory.models import PurchaseOrder
    supplier = get_object_or_404(Supplier, pk=pk)
    orders = PurchaseOrder.objects.filter(supplier=supplier).order_by('-order_date')[:10]
    # Items supplied (via PO)
    from inventory.models import PurchaseItem
    item_ids = PurchaseItem.objects.filter(
        purchase_order__supplier=supplier
    ).values_list('inventory_item_id', flat=True).distinct()
    items_supplied = InventoryItem.objects.filter(pk__in=item_ids)
    return render(request, 'inventory/supplier_detail.html', {
        'supplier': supplier,
        'orders': orders,
        'items_supplied': items_supplied,
    })

@login_required
@role_required('inventory')
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        p = request.POST
        supplier.name           = p.get('name', supplier.name)
        supplier.contact_person = p.get('contact_person', supplier.contact_person)
        supplier.phone          = p.get('phone', supplier.phone)
        supplier.email          = p.get('email', supplier.email)
        supplier.address        = p.get('address', supplier.address)
        supplier.is_active      = bool(p.get('is_active'))
        supplier.save()
        messages.success(request, f'Supplier {supplier.name} updated.')
        return redirect('supplier_detail', pk=pk)
    return render(request, 'inventory/supplier_form.html', {'supplier': supplier})

@login_required
@role_required('inventory')
def item_toggle_active(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.is_active = not item.is_active
        item.save()
        status = "activated" if item.is_active else "deactivated"
        messages.success(request, f"{item.name} has been {status}.")
    return redirect('item_detail', pk=pk)
