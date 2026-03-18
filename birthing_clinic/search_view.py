from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.permissions import role_required

@login_required
@role_required('patient_view')
def global_search(request):
    q = request.GET.get('q', '').strip()
    results = {'patients': [], 'bills': [], 'deliveries': [], 'newborns': []}
    total = 0

    if q and len(q) >= 2:
        from patients.models import Patient
        from billing.models import Bill
        from delivery.models import DeliveryRecord
        from newborn.models import NewbornRecord
        from django.db.models import Q

        # Patients
        patients = Patient.objects.filter(
            Q(full_name__icontains=q) |
            Q(record_number__icontains=q) |
            Q(contact_number__icontains=q) |
            Q(partner_name__icontains=q)
        ).order_by('full_name')[:10]
        results['patients'] = patients
        total += patients.count()

        # Bills
        bills = Bill.objects.filter(
            Q(bill_number__icontains=q) |
            Q(patient__full_name__icontains=q) |
            Q(patient__record_number__icontains=q)
        ).select_related('patient').order_by('-billing_date')[:10]
        results['bills'] = bills
        total += bills.count()

        # Deliveries
        deliveries = DeliveryRecord.objects.filter(
            Q(patient__full_name__icontains=q) |
            Q(patient__record_number__icontains=q)
        ).select_related('patient').order_by('-admission_datetime')[:5]
        results['deliveries'] = deliveries
        total += deliveries.count()

        # Newborns
        newborns = NewbornRecord.objects.filter(
            Q(baby_id__icontains=q) |
            Q(baby_name__icontains=q) |
            Q(mother__full_name__icontains=q)
        ).select_related('mother').order_by('-birth_datetime')[:5]
        results['newborns'] = newborns
        total += newborns.count()

    return render(request, 'search_results.html', {
        'q': q, 'results': results, 'total': total
    })
