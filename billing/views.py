from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.permissions import role_required
from .models import Bill, BillItem, Payment
from patients.models import Patient

@login_required
@role_required('billing_view')
def bill_list(request):
    status = request.GET.get('status', '')
    bills = Bill.objects.filter(is_active=True).select_related('patient').order_by('-created_at')
    if status:
        bills = bills.filter(payment_status=status)
    return render(request, 'billing/bill_list.html', {'bills': bills, 'status_filter': status})

@login_required
@role_required('billing')
def bill_add(request):
    patients = Patient.objects.filter(is_active=True).order_by('full_name')
    if request.method == 'POST':
        p = request.POST
        patient = get_object_or_404(Patient, pk=p.get('patient'))
        bill = Bill.objects.create(
            patient=patient, notes=p.get('notes', ''), cashier=request.user,
            discount=p.get('discount', 0) or 0,
            discount_reason=p.get('discount_reason', ''),
        )
        # Add bill items
        descs = request.POST.getlist('description[]')
        types = request.POST.getlist('item_type[]')
        qtys = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('unit_price[]')
        for d, t, q, up in zip(descs, types, qtys, prices):
            if d and up:
                from decimal import Decimal
                BillItem.objects.create(
                    bill=bill, description=d, item_type=t,
                    quantity=Decimal(str(q or 1)), unit_price=Decimal(str(up or 0))
                )
        bill.recalculate_totals()
        messages.success(request, f'Bill {bill.bill_number} created.')
        return redirect('bill_detail', pk=bill.pk)
    return render(request, 'billing/bill_form.html', {'patients': patients})

@login_required
@role_required('billing_view')
def bill_detail(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    payments = bill.payments.all().order_by('-payment_date')
    return render(request, 'billing/bill_detail.html', {'bill': bill, 'payments': payments})

@login_required
@role_required('billing')
def add_payment(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        p = request.POST
        from decimal import Decimal
        amount = Decimal(str(p.get('amount', 0) or 0))
        Payment.objects.create(
            bill=bill, amount=amount,
            payment_method=p.get('payment_method', 'cash'),
            reference_number=p.get('reference_number', ''),
            received_by=request.user,
            notes=p.get('notes', ''),
        )
        messages.success(request, f'Payment of ₱{amount:,.2f} recorded.')
        return redirect('bill_detail', pk=pk)
    return redirect('bill_detail', pk=pk)

@login_required
@role_required('billing_view')
def print_receipt(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    payments = bill.payments.all().order_by('-payment_date')
    return render(request, 'billing/receipt.html', {'bill': bill, 'payments': payments})

@login_required
@role_required('billing')
def bill_edit(request, pk):
    from decimal import Decimal
    bill = get_object_or_404(Bill, pk=pk)
    patients = Patient.objects.filter(is_active=True).order_by('full_name')
    if bill.payment_status == 'paid':
        messages.error(request, 'Cannot edit a fully paid bill.')
        return redirect('bill_detail', pk=pk)
    if request.method == 'POST':
        p = request.POST
        bill.discount = p.get('discount', 0) or 0
        bill.discount_reason = p.get('discount_reason', bill.discount_reason)
        bill.notes = p.get('notes', bill.notes)
        # Replace all items
        bill.bill_items.all().delete()
        descs  = request.POST.getlist('description[]')
        types  = request.POST.getlist('item_type[]')
        qtys   = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('unit_price[]')
        for d, t, q, up in zip(descs, types, qtys, prices):
            if d and up:
                BillItem.objects.create(
                    bill=bill, description=d, item_type=t,
                    quantity=Decimal(str(q or 1)),
                    unit_price=Decimal(str(up or 0))
                )
        bill.recalculate_totals()
        messages.success(request, f'Bill {bill.bill_number} updated.')
        return redirect('bill_detail', pk=pk)
    return render(request, 'billing/bill_edit.html', {'bill': bill, 'patients': patients})

@login_required
@role_required('billing')
def waive_bill(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        bill.payment_status = 'waived'
        bill.notes = (bill.notes + '\n' + request.POST.get('waive_reason', '')).strip()
        bill.save()
        messages.success(request, f'Bill {bill.bill_number} marked as waived.')
    return redirect('bill_detail', pk=pk)

@login_required
@role_required('billing')
def bill_from_delivery(request, delivery_pk):
    """Pre-fill a new bill from a delivery record."""
    from delivery.models import DeliveryRecord
    delivery = get_object_or_404(DeliveryRecord, pk=delivery_pk)
    patients = Patient.objects.filter(is_active=True).order_by('full_name')
    # Pre-built items based on delivery type
    preset_items = [
        {'desc': 'Delivery Fee', 'type': 'service', 'qty': 1, 'price': 0},
        {'desc': 'Room & Board', 'type': 'room', 'qty': 1, 'price': 0},
        {'desc': 'Newborn Care', 'type': 'service', 'qty': delivery.newborns.count() or 1, 'price': 0},
        {'desc': 'Medicines & Supplies', 'type': 'supply', 'qty': 1, 'price': 0},
    ]
    if delivery.delivery_type == 'cs':
        preset_items.insert(0, {'desc': 'Operating Room Fee', 'type': 'procedure', 'qty': 1, 'price': 0})
    if request.method == 'POST':
        p = request.POST
        bill = Bill.objects.create(
            patient=delivery.patient,
            delivery_record=delivery,
            discount=p.get('discount', 0) or 0,
            discount_reason=p.get('discount_reason', ''),
            notes=p.get('notes', ''),
            cashier=request.user,
        )
        descs  = request.POST.getlist('description[]')
        types  = request.POST.getlist('item_type[]')
        qtys   = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('unit_price[]')
        from decimal import Decimal
        for d, t, q, up in zip(descs, types, qtys, prices):
            if d and up:
                BillItem.objects.create(
                    bill=bill, description=d, item_type=t,
                    quantity=Decimal(str(q or 1)),
                    unit_price=Decimal(str(up or 0))
                )
        bill.recalculate_totals()
        messages.success(request, f'Bill {bill.bill_number} created from delivery record.')
        return redirect('bill_detail', pk=bill.pk)
    return render(request, 'billing/bill_from_delivery.html', {
        'delivery': delivery,
        'preset_items': preset_items,
        'patients': patients,
    })

# ── PhilHealth Claims ───────────────────────────────────────────────────────
@login_required
@role_required('billing_view')
def philhealth_list(request):
    from billing.models import PhilHealthClaim
    status = request.GET.get('status', '')
    claims = PhilHealthClaim.objects.select_related('patient', 'bill').order_by('-date_of_service')
    if status:
        claims = claims.filter(status=status)
    # Summary stats
    from django.db.models import Sum, Count
    stats = claims.aggregate(
        total_claims=Count('id'),
        total_amount=Sum('case_rate_amount'),
        total_reimbursed=Sum('amount_reimbursed'),
    )
    return render(request, 'billing/philhealth_list.html', {
        'claims': claims[:100],
        'status_filter': status,
        'stats': stats,
        'status_choices': PhilHealthClaim.STATUS_CHOICES,
    })

@login_required
@role_required('billing')
def philhealth_add(request):
    from billing.models import PhilHealthClaim
    patients = Patient.objects.filter(is_active=True).order_by('full_name')
    bills = Bill.objects.filter(payment_status__in=['unpaid','partial']).order_by('-billing_date')
    if request.method == 'POST':
        p = request.POST
        PhilHealthClaim.objects.create(
            patient_id=p.get('patient'),
            bill_id=p.get('bill') or None,
            claim_number=p.get('claim_number', ''),
            case_rate_type=p.get('case_rate_type'),
            case_rate_amount=p.get('case_rate_amount', 0) or 0,
            member_pin=p.get('member_pin', ''),
            date_of_service=p.get('date_of_service'),
            notes=p.get('notes', ''),
        )
        messages.success(request, 'PhilHealth claim created.')
        return redirect('philhealth_list')
    return render(request, 'billing/philhealth_form.html', {
        'patients': patients, 'bills': bills,
        'case_rates': PhilHealthClaim.CASE_RATES,
    })

@login_required
@role_required('billing')
def philhealth_update(request, pk):
    from billing.models import PhilHealthClaim
    claim = get_object_or_404(PhilHealthClaim, pk=pk)
    if request.method == 'POST':
        p = request.POST
        claim.status            = p.get('status', claim.status)
        claim.claim_number      = p.get('claim_number', claim.claim_number)
        claim.date_submitted    = p.get('date_submitted') or claim.date_submitted
        claim.date_approved     = p.get('date_approved') or claim.date_approved
        claim.amount_reimbursed = p.get('amount_reimbursed', claim.amount_reimbursed) or 0
        claim.rejection_reason  = p.get('rejection_reason', claim.rejection_reason)
        claim.notes             = p.get('notes', claim.notes)
        claim.save()
        messages.success(request, f'Claim updated — status: {claim.get_status_display()}')
        return redirect('philhealth_list')
    return render(request, 'billing/philhealth_update.html', {
        'claim': claim,
        'status_choices': PhilHealthClaim.STATUS_CHOICES,
    })


# ── End-of-Day Cash Close ───────────────────────────────────────────────────
@login_required
@role_required('billing_view')
def eod_report(request):
    from billing.models import Payment, Bill
    from django.db.models import Sum, Count
    from datetime import date as dt
    report_date = request.GET.get('date', str(dt.today()))
    try:
        from datetime import datetime
        rdate = datetime.strptime(report_date, '%Y-%m-%d').date()
    except:
        rdate = dt.today()

    payments = Payment.objects.filter(
        payment_date__date=rdate
    ).select_related('bill__patient', 'received_by').order_by('payment_date')

    summary = payments.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')

    totals = payments.aggregate(count=Count('id'), total=Sum('amount'))
    new_bills = Bill.objects.filter(billing_date=rdate)
    new_bills_total = new_bills.aggregate(t=Sum('total_amount'))['t'] or 0
    outstanding = Bill.objects.filter(
        payment_status__in=['unpaid','partial']
    ).aggregate(t=Sum('balance'))['t'] or 0

    return render(request, 'billing/eod_report.html', {
        'report_date': rdate,
        'payments': payments,
        'summary': summary,
        'totals': totals,
        'new_bills': new_bills,
        'new_bills_total': new_bills_total,
        'outstanding': outstanding,
    })
