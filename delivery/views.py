from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime as _parse_dt
from accounts.permissions import role_required
from .models import DeliveryRecord, LaborMonitoring, DeliveryComplication
from patients.models import Patient

def _parse_aware(dt_str):
    if not dt_str:
        return None
    dt = _parse_dt(dt_str)
    if dt and timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt

@login_required
@role_required('clinical')
def delivery_list(request):
    deliveries = DeliveryRecord.objects.select_related('patient').filter(is_active=True).order_by('-admission_datetime')
    return render(request, 'delivery/delivery_list.html', {'deliveries': deliveries})

@login_required
@role_required('delivery')
def delivery_admit(request):
    from accounts.models import StaffProfile
    from django.contrib.auth.models import User
    patients = Patient.objects.filter(is_active=True).order_by('full_name')
    doctors = StaffProfile.objects.filter(role__in=['doctor','admin','super_admin'], is_active=True).select_related('user')
    midwives = StaffProfile.objects.filter(role__in=['midwife','nurse','admin','super_admin'], is_active=True).select_related('user')
    if request.method == 'POST':
        p = request.POST
        patient = get_object_or_404(Patient, pk=p.get('patient'))
        doctor = User.objects.filter(pk=p.get('attending_doctor') or 0).first()
        midwife_id = p.get('attending_midwife_select')
        midwife = User.objects.filter(pk=midwife_id or 0).first() or request.user
        delivery = DeliveryRecord.objects.create(
            patient=patient,
            admission_datetime=_parse_aware(p.get('admission_datetime')) or timezone.now(),
            chief_complaint=p.get('chief_complaint', ''),
            attending_midwife=midwife,
            attending_doctor=doctor,
            notes=p.get('notes', ''),
        )
        messages.success(request, f'Patient {patient.full_name} admitted for labor.')
        return redirect('delivery_detail', pk=delivery.pk)
    return render(request, 'delivery/delivery_admit.html', {
        'patients': patients, 'doctors': doctors, 'midwives': midwives
    })

@login_required
@role_required('clinical')
def delivery_detail(request, pk):
    from accounts.models import StaffProfile
    from django.contrib.auth.models import User as AuthUser
    delivery = get_object_or_404(DeliveryRecord, pk=pk)
    monitoring = delivery.labor_monitoring.all().order_by('-recorded_at')
    complications = delivery.complication_records.all().order_by('-recorded_at')
    doctors = StaffProfile.objects.filter(role__in=['doctor','admin','super_admin'], is_active=True).select_related('user')
    midwives = StaffProfile.objects.filter(role__in=['midwife','nurse','admin','super_admin'], is_active=True).select_related('user')
    if request.method == 'POST':
        p = request.POST
        delivery.delivery_type = p.get('delivery_type') or delivery.delivery_type
        delivery.presentation = p.get('presentation') or delivery.presentation
        delivery.complications = p.get('complications', delivery.complications)
        delivery.maternal_condition = p.get('maternal_condition', delivery.maternal_condition)
        delivery.notes = p.get('notes', delivery.notes)
        doc_id = p.get('attending_doctor')
        if doc_id:
            delivery.attending_doctor = AuthUser.objects.filter(pk=doc_id).first()
        mid_id = p.get('attending_midwife_select')
        if mid_id:
            delivery.attending_midwife = AuthUser.objects.filter(pk=mid_id).first()
        delivery.estimated_blood_loss = p.get('ebl') or delivery.estimated_blood_loss
        labor_start = _parse_aware(p.get('labor_start_time'))
        if labor_start:
            delivery.labor_start_time = labor_start
        full_dil = _parse_aware(p.get('full_dilation_time'))
        if full_dil:
            delivery.full_dilation_time = full_dil
        placenta = _parse_aware(p.get('placenta_delivery_time'))
        if placenta:
            delivery.placenta_delivery_time = placenta
        dt = _parse_aware(p.get('delivery_datetime'))
        if dt:
            delivery.delivery_datetime = dt
        discharge_dt = _parse_aware(p.get('discharge_datetime'))
        if discharge_dt:
            delivery.discharge_datetime = discharge_dt
        delivery.save()
        messages.success(request, 'Delivery record updated.')
        return redirect('delivery_detail', pk=pk)
    return render(request, 'delivery/delivery_detail.html', {
        'delivery': delivery,
        'monitoring': monitoring,
        'complications': complications,
        'doctors': doctors,
        'midwives': midwives,
    })

@login_required
@role_required('delivery')
def add_complication(request, pk):
    delivery = get_object_or_404(DeliveryRecord, pk=pk)
    if request.method == 'POST':
        p = request.POST
        DeliveryComplication.objects.create(
            delivery_record=delivery,
            complication_type=p.get('complication_type', 'other'),
            description=p.get('description', ''),
            action_taken=p.get('action_taken', ''),
            recorded_by=request.user,
        )
        messages.success(request, 'Complication recorded.')
    return redirect('delivery_detail', pk=pk)

@login_required
@role_required('clinical')
def labor_monitor(request, pk):
    delivery = get_object_or_404(DeliveryRecord, pk=pk)
    monitoring = delivery.labor_monitoring.all().order_by('recorded_at')
    return render(request, 'delivery/labor_monitor.html', {'delivery': delivery, 'monitoring': monitoring})

@login_required
@role_required('delivery')
def add_monitoring(request, pk):
    delivery = get_object_or_404(DeliveryRecord, pk=pk)
    if request.method == 'POST':
        p = request.POST
        LaborMonitoring.objects.create(
            delivery_record=delivery,
            recorded_at=_parse_aware(p.get('recorded_at')) or timezone.now(),
            contraction_frequency=p.get('contraction_frequency', ''),
            contraction_duration=p.get('contraction_duration', ''),
            fetal_heart_rate=p.get('fhr') or None,
            cervical_dilation=p.get('dilation') or None,
            maternal_bp_systolic=p.get('bp_systolic') or None,
            maternal_bp_diastolic=p.get('bp_diastolic') or None,
            maternal_pulse=p.get('pulse') or None,
            membrane_status=p.get('membrane_status', 'intact'),
            notes=p.get('notes', ''),
            recorded_by=request.user,
        )
        messages.success(request, 'Monitoring entry added.')
    return redirect('delivery_detail', pk=pk)
