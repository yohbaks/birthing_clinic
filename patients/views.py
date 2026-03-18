from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.permissions import role_required
from .models import Patient, EmergencyContact, PregnancyHistory

@login_required
@role_required('patient_view')
def patient_list(request):
    q = request.GET.get('q', '')
    risk = request.GET.get('risk', '')
    patients = Patient.objects.filter(is_active=True)
    if q:
        patients = patients.filter(
            Q(full_name__icontains=q) | Q(record_number__icontains=q) |
            Q(contact_number__icontains=q) | Q(address__icontains=q)
        )
    if risk:
        patients = patients.filter(risk_level=risk)
    return render(request, 'patients/patient_list.html', {
        'patients': patients, 'query': q, 'risk_filter': risk
    })

@login_required
@role_required('clinical')
def patient_add(request):
    if request.method == 'POST':
        p = request.POST
        patient = Patient.objects.create(
            full_name=p.get('full_name', ''),
            date_of_birth=p.get('date_of_birth'),
            civil_status=p.get('civil_status', 'single'),
            contact_number=p.get('contact_number', ''),
            address=p.get('address', ''),
            partner_name=p.get('partner_name', ''),
            blood_type=p.get('blood_type', ''),
            allergies=p.get('allergies', ''),
            existing_conditions=p.get('existing_conditions', ''),
            risk_level=p.get('risk_level', 'low'),
            gravida=int(p.get('gravida', 0) or 0),
            para=int(p.get('para', 0) or 0),
            abortion_history=int(p.get('abortion_history', 0) or 0),
            lmp=p.get('lmp') or None,
            edd=p.get('edd') or None,
            notes=p.get('notes', ''),
        )
        # Emergency contact
        if p.get('ec_name'):
            EmergencyContact.objects.create(
                patient=patient,
                name=p.get('ec_name', ''),
                relationship=p.get('ec_relationship', ''),
                contact_number=p.get('ec_contact', ''),
                address=p.get('ec_address', ''),
            )
        messages.success(request, f'Patient {patient.full_name} registered. Record: {patient.record_number}')
        return redirect('patient_profile', pk=patient.pk)
    return render(request, 'patients/patient_form.html', {'action': 'Register'})

@login_required
@role_required('patient_view')
def patient_profile(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    context = {
        'patient': patient,
        'prenatal_visits': patient.prenatal_visits.all()[:5],
        'deliveries': patient.deliveries.all()[:5],
        'appointments': patient.appointments.filter(status__in=['pending','confirmed']).order_by('date')[:5],
        'bills': patient.bills.filter(is_active=True).order_by('-created_at')[:5],
        'emergency_contacts': patient.emergency_contacts.all(),
        'pregnancy_history': patient.pregnancy_history.all().order_by('-year'),
        'ultrasounds': patient.ultrasounds.all().order_by('-date')[:5],
    }
    return render(request, 'patients/patient_profile.html', context)

@login_required
@role_required('clinical')
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        p = request.POST
        patient.full_name = p.get('full_name', patient.full_name)
        patient.date_of_birth = p.get('date_of_birth', patient.date_of_birth)
        patient.civil_status = p.get('civil_status', patient.civil_status)
        patient.contact_number = p.get('contact_number', patient.contact_number)
        patient.address = p.get('address', patient.address)
        patient.partner_name = p.get('partner_name', patient.partner_name)
        patient.blood_type = p.get('blood_type', patient.blood_type)
        patient.allergies = p.get('allergies', patient.allergies)
        patient.existing_conditions = p.get('existing_conditions', patient.existing_conditions)
        patient.risk_level = p.get('risk_level', patient.risk_level)
        patient.gravida = int(p.get('gravida', patient.gravida) or patient.gravida)
        patient.para = int(p.get('para', patient.para) or patient.para)
        patient.abortion_history = int(p.get('abortion_history', patient.abortion_history) or patient.abortion_history)
        patient.lmp = p.get('lmp') or patient.lmp
        patient.edd = p.get('edd') or patient.edd
        patient.notes = p.get('notes', patient.notes)
        patient.save()
        messages.success(request, 'Patient record updated.')
        return redirect('patient_profile', pk=pk)
    return render(request, 'patients/patient_form.html', {'patient': patient, 'action': 'Edit'})

@login_required
@role_required('clinical')
def add_pregnancy_history(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        p = request.POST
        PregnancyHistory.objects.create(
            patient=patient,
            year=p.get('year'),
            delivery_type=p.get('delivery_type', ''),
            outcome=p.get('outcome', ''),
            birth_weight=(lambda v: float(''.join(c for c in v if c.isdigit() or c == '.')) if v else None)(p.get('birth_weight', '')) or None,
            complications=p.get('complications', ''),
            notes=p.get('notes', ''),
        )
        messages.success(request, 'Pregnancy history added.')
    return redirect('patient_profile', pk=pk)

@login_required
@role_required('admin')
def deactivate_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        patient.is_active = False
        patient.save()
        messages.success(request, f'{patient.full_name} has been deactivated.')
        return redirect('patient_list')
    return render(request, 'patients/patient_confirm_deactivate.html', {'patient': patient})

@login_required
@role_required('admin')
def reactivate_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk, is_active=False)
    if request.method == 'POST':
        patient.is_active = True
        patient.save()
        messages.success(request, f'{patient.full_name} has been reactivated.')
        return redirect('patient_profile', pk=pk)
    return render(request, 'patients/patient_confirm_reactivate.html', {'patient': patient})

@login_required
@role_required('admin')
def inactive_patients(request):
    patients = Patient.objects.filter(is_active=False).order_by('full_name')
    return render(request, 'patients/inactive_patients.html', {'patients': patients})

@login_required
def check_duplicate_patient(request):
    """AJAX endpoint — returns similar patient names."""
    from django.http import JsonResponse
    from django.db.models import Q
    name = request.GET.get('name', '').strip()
    if len(name) < 3:
        return JsonResponse({'duplicates': []})
    # Split name into parts for flexible matching
    parts = name.split()
    q = Q()
    for part in parts:
        if len(part) >= 3:
            q |= Q(full_name__icontains=part)
    matches = Patient.objects.filter(q, is_active=True).exclude(
        full_name__iexact=name  # Exact match handled separately
    ).values('pk', 'full_name', 'record_number', 'date_of_birth')[:5]
    # Also check exact match
    exact = Patient.objects.filter(full_name__iexact=name, is_active=True).values(
        'pk', 'full_name', 'record_number', 'date_of_birth'
    )[:3]
    all_matches = list(exact) + [m for m in matches if m not in list(exact)]
    # Format dates
    for m in all_matches:
        if m.get('date_of_birth'):
            m['date_of_birth'] = str(m['date_of_birth'])
    return JsonResponse({'duplicates': all_matches[:5], 'has_exact': len(exact) > 0})

@login_required
@role_required('clinical_staff')
def add_maternal_immunization(request, pk):
    from .models import MaternalImmunization
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        p = request.POST
        MaternalImmunization.objects.create(
            patient=patient,
            vaccine=p.get('vaccine'),
            date_given=p.get('date_given'),
            given_by=p.get('given_by', ''),
            facility=p.get('facility', ''),
            notes=p.get('notes', ''),
        )
        messages.success(request, f'Immunization record added for {patient.full_name}.')
    return redirect('patient_profile', pk=pk)

@login_required
@role_required('clinical_staff')
def delete_maternal_immunization(request, pk):
    from .models import MaternalImmunization
    imm = get_object_or_404(MaternalImmunization, pk=pk)
    patient_pk = imm.patient.pk
    if request.method == 'POST':
        imm.delete()
        messages.success(request, 'Immunization record deleted.')
    return redirect('patient_profile', pk=patient_pk)

@login_required
@role_required('clinical')
def import_patients_csv(request):
    """Bulk import patients from CSV file."""
    import csv, io
    results = {'created': 0, 'skipped': 0, 'errors': []}
    if request.method == 'POST' and request.FILES.get('csv_file'):
        f = request.FILES['csv_file']
        try:
            decoded = f.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded))
            for i, row in enumerate(reader, 1):
                try:
                    name = row.get('full_name','').strip() or row.get('Full Name','').strip()
                    dob  = row.get('date_of_birth','').strip() or row.get('Date of Birth','').strip()
                    if not name or not dob:
                        results['skipped'] += 1
                        continue
                    if Patient.objects.filter(full_name__iexact=name).exists():
                        results['skipped'] += 1
                        continue
                    Patient.objects.create(
                        full_name=name,
                        date_of_birth=dob,
                        civil_status=row.get('civil_status','single') or 'single',
                        contact_number=row.get('contact_number','').strip(),
                        address=row.get('address','').strip(),
                        blood_type=row.get('blood_type','').strip(),
                        risk_level=row.get('risk_level','low') or 'low',
                        gravida=int(row.get('gravida',0) or 0),
                        para=int(row.get('para',0) or 0),
                        abortion_history=int(row.get('abortion_history',0) or 0),
                        allergies=row.get('allergies','').strip(),
                        existing_conditions=row.get('existing_conditions','').strip(),
                        partner_name=row.get('partner_name','').strip(),
                    )
                    results['created'] += 1
                except Exception as e:
                    results['errors'].append(f"Row {i}: {str(e)[:80]}")
            messages.success(request, f"Import complete: {results['created']} created, {results['skipped']} skipped, {len(results['errors'])} errors.")
        except Exception as e:
            messages.error(request, f'Error reading file: {e}')
    return render(request, 'patients/import_csv.html', {'results': results if request.method == 'POST' else None})
