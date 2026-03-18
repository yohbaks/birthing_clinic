from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime as _parse_dt
from accounts.permissions import role_required
from .models import NewbornRecord, NewbornImmunization
from patients.models import Patient
from delivery.models import DeliveryRecord

def _parse_aware(dt_str):
    if not dt_str:
        return None
    dt = _parse_dt(dt_str)
    if dt and timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt

@login_required
@role_required('clinical')
def newborn_list(request):
    newborns = NewbornRecord.objects.select_related('mother').order_by('-birth_datetime')
    return render(request, 'newborn/newborn_list.html', {'newborns': newborns})

@login_required
@role_required('delivery')
def newborn_add(request):
    patients = Patient.objects.filter(is_active=True).order_by('full_name')
    deliveries = DeliveryRecord.objects.filter(is_active=True).order_by('-admission_datetime')
    if request.method == 'POST':
        p = request.POST
        patient = get_object_or_404(Patient, pk=p.get('mother'))
        delivery = get_object_or_404(DeliveryRecord, pk=p.get('delivery_record'))
        nb = NewbornRecord.objects.create(
            mother=patient,
            delivery_record=delivery,
            baby_name=p.get('baby_name', ''),
            gender=p.get('gender', 'male'),
            birth_status=p.get('birth_status', 'alive'),
            birth_datetime=_parse_aware(p.get('birth_datetime')) or timezone.now(),
            weight_grams=p.get('weight_grams', 0),
            length_cm=p.get('length_cm', 0),
            head_circumference_cm=p.get('head_circumference') or None,
            apgar_1min=p.get('apgar_1min') or None,
            apgar_5min=p.get('apgar_5min') or None,
            vitamin_k_given=bool(p.get('vitamin_k_given')),
            eye_prophylaxis_given=bool(p.get('eye_prophylaxis_given')),
            newborn_screening_done=bool(p.get('newborn_screening_done')),
            notes=p.get('notes', ''),
        )
        messages.success(request, f'Newborn record {nb.baby_id} created.')
        return redirect('newborn_detail', pk=nb.pk)
    return render(request, 'newborn/newborn_form.html', {'patients': patients, 'deliveries': deliveries})

@login_required
@role_required('clinical')
def newborn_detail(request, pk):
    newborn = get_object_or_404(NewbornRecord, pk=pk)
    immunizations = newborn.immunizations.all().order_by('date_given')
    return render(request, 'newborn/newborn_detail.html', {
        'newborn': newborn,
        'immunizations': immunizations,
    })

@login_required
@role_required('delivery')
def add_immunization(request, pk):
    newborn = get_object_or_404(NewbornRecord, pk=pk)
    if request.method == 'POST':
        p = request.POST
        NewbornImmunization.objects.create(
            newborn=newborn,
            vaccine_name=p.get('vaccine_name', ''),
            date_given=p.get('date_given'),
            dose=p.get('dose', ''),
            administered_by=p.get('administered_by', ''),
            notes=p.get('notes', ''),
        )
        messages.success(request, f'Immunization recorded.')
    return redirect('newborn_detail', pk=pk)

@login_required
@role_required('delivery')
def discharge_newborn(request, pk):
    newborn = get_object_or_404(NewbornRecord, pk=pk)
    if request.method == 'POST':
        p = request.POST
        newborn.discharge_datetime = _parse_aware(p.get('discharge_datetime')) or timezone.now()
        newborn.discharge_weight_grams = p.get('discharge_weight') or newborn.discharge_weight_grams
        newborn.notes = (newborn.notes + '\n' + p.get('discharge_notes', '')).strip()
        newborn.save()
        messages.success(request, 'Newborn discharged.')
    return redirect('newborn_detail', pk=pk)

@login_required
@role_required('delivery')
def newborn_edit(request, pk):
    newborn = get_object_or_404(NewbornRecord, pk=pk)
    if request.method == 'POST':
        p = request.POST
        newborn.baby_name       = p.get('baby_name', newborn.baby_name)
        newborn.gender          = p.get('gender', newborn.gender)
        newborn.birth_status    = p.get('birth_status', newborn.birth_status)
        newborn.birth_datetime  = _parse_aware(p.get('birth_datetime')) or newborn.birth_datetime
        newborn.weight_grams    = p.get('weight_grams', newborn.weight_grams)
        newborn.length_cm       = p.get('length_cm', newborn.length_cm)
        newborn.head_circumference_cm = p.get('head_circumference') or newborn.head_circumference_cm
        newborn.apgar_1min      = p.get('apgar_1min') or newborn.apgar_1min
        newborn.apgar_5min      = p.get('apgar_5min') or newborn.apgar_5min
        newborn.vitamin_k_given         = bool(p.get('vitamin_k_given'))
        newborn.eye_prophylaxis_given   = bool(p.get('eye_prophylaxis_given'))
        newborn.newborn_screening_done  = bool(p.get('newborn_screening_done'))
        newborn.initial_diagnosis       = p.get('initial_diagnosis', newborn.initial_diagnosis)
        newborn.notes           = p.get('notes', newborn.notes)
        newborn.save()
        messages.success(request, f'Newborn record {newborn.baby_id} updated.')
        return redirect('newborn_detail', pk=pk)
    return render(request, 'newborn/newborn_edit.html', {'newborn': newborn})
