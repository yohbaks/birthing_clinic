import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.permissions import role_required
from .models import PostpartumVisit
from patients.models import Patient


@login_required
@role_required('clinical')
def postpartum_list(request):
    visits = PostpartumVisit.objects.select_related(
        'patient', 'delivery_record'
    ).order_by('-visit_date')
    # Filter
    q = request.GET.get('q', '')
    vtype = request.GET.get('type', '')
    if q:
        visits = visits.filter(patient__full_name__icontains=q)
    if vtype:
        visits = visits.filter(visit_type=vtype)
    # Alert: patients due for 6-week visit
    from datetime import date, timedelta
    from delivery.models import DeliveryRecord
    cutoff_start = date.today() - timedelta(days=50)
    cutoff_end   = date.today() - timedelta(days=35)
    due_for_6wk = DeliveryRecord.objects.filter(
        delivery_datetime__date__range=[cutoff_start, cutoff_end]
    ).exclude(
        patient__postpartum_visits__visit_type='6week'
    ).select_related('patient').distinct()[:10]
    return render(request, 'postpartum/postpartum_list.html', {
        'visits': visits[:100],
        'q': q, 'vtype': vtype,
        'visit_types': PostpartumVisit.VISIT_TYPES,
        'due_for_6wk': due_for_6wk,
    })


@login_required
@role_required('clinical_staff')
def postpartum_add(request):
    patients = Patient.objects.filter(is_active=True).order_by('full_name')
    from delivery.models import DeliveryRecord
    # Pre-fill from URL params
    patient_id  = request.GET.get('patient', '')
    delivery_id = request.GET.get('delivery', '')
    if request.method == 'POST':
        p = request.POST
        patient = get_object_or_404(Patient, pk=p.get('patient'))
        visit = PostpartumVisit.objects.create(
            patient=patient,
            delivery_record_id=p.get('delivery_record') or None,
            visit_date=p.get('visit_date'),
            visit_type=p.get('visit_type', '6week'),
            days_postpartum=p.get('days_postpartum') or None,
            blood_pressure_systolic=p.get('bp_systolic') or None,
            blood_pressure_diastolic=p.get('bp_diastolic') or None,
            temperature=p.get('temperature') or None,
            weight=p.get('weight') or None,
            pulse=p.get('pulse') or None,
            uterine_involution=p.get('uterine_involution', ''),
            lochia=p.get('lochia', ''),
            wound_status=p.get('wound_status', ''),
            breast_condition=p.get('breast_condition', ''),
            breastfeeding=p.get('breastfeeding', 'exclusive'),
            perineum_status=p.get('perineum_status', ''),
            mood_score=p.get('mood_score') or None,
            mood_notes=p.get('mood_notes', ''),
            fp_counseled=bool(p.get('fp_counseled')),
            fp_method_chosen=p.get('fp_method_chosen', 'none'),
            fp_method_provided=bool(p.get('fp_method_provided')),
            newborn_weight=p.get('newborn_weight') or None,
            newborn_condition=p.get('newborn_condition', ''),
            newborn_feeding=p.get('newborn_feeding', ''),
            chief_complaint=p.get('chief_complaint', ''),
            assessment=p.get('assessment', ''),
            plan=p.get('plan', ''),
            prescribed_medicines=p.get('prescribed_medicines', ''),
            referral=p.get('referral', ''),
            follow_up_date=p.get('follow_up_date') or None,
            notes=p.get('notes', ''),
            attending_staff=request.user,
        )
        messages.success(request, f'Postpartum visit recorded for {patient.full_name}.')
        return redirect('postpartum_detail', pk=visit.pk)
    # Prefill delivery records for selected patient
    deliveries = DeliveryRecord.objects.filter(
        patient_id=patient_id
    ).order_by('-admission_datetime') if patient_id else []
    return render(request, 'postpartum/postpartum_form.html', {
        'patients': patients,
        'deliveries': deliveries,
        'patient_id': patient_id,
        'delivery_id': delivery_id,
        'visit_types': PostpartumVisit.VISIT_TYPES,
        'breastfeeding_choices': PostpartumVisit.BREASTFEEDING,
        'fp_choices': PostpartumVisit.FP_METHODS,
        'today': timezone.now().date(),
    })


@login_required
@role_required('clinical')
def postpartum_detail(request, pk):
    visit = get_object_or_404(PostpartumVisit, pk=pk)
    # All visits for this patient for context
    all_visits = PostpartumVisit.objects.filter(
        patient=visit.patient
    ).order_by('visit_date')
    return render(request, 'postpartum/postpartum_detail.html', {
        'visit': visit,
        'all_visits': all_visits,
    })


@login_required
@role_required('clinical_staff')
def postpartum_edit(request, pk):
    visit = get_object_or_404(PostpartumVisit, pk=pk)
    patients = Patient.objects.filter(is_active=True).order_by('full_name')
    from delivery.models import DeliveryRecord
    deliveries = DeliveryRecord.objects.filter(
        patient=visit.patient
    ).order_by('-admission_datetime')
    if request.method == 'POST':
        p = request.POST
        visit.visit_date     = p.get('visit_date', visit.visit_date)
        visit.visit_type     = p.get('visit_type', visit.visit_type)
        visit.days_postpartum= p.get('days_postpartum') or visit.days_postpartum
        visit.blood_pressure_systolic  = p.get('bp_systolic') or visit.blood_pressure_systolic
        visit.blood_pressure_diastolic = p.get('bp_diastolic') or visit.blood_pressure_diastolic
        visit.temperature    = p.get('temperature') or visit.temperature
        visit.weight         = p.get('weight') or visit.weight
        visit.pulse          = p.get('pulse') or visit.pulse
        visit.uterine_involution = p.get('uterine_involution', visit.uterine_involution)
        visit.lochia         = p.get('lochia', visit.lochia)
        visit.wound_status   = p.get('wound_status', visit.wound_status)
        visit.breast_condition = p.get('breast_condition', visit.breast_condition)
        visit.breastfeeding  = p.get('breastfeeding', visit.breastfeeding)
        visit.mood_score     = p.get('mood_score') or visit.mood_score
        visit.mood_notes     = p.get('mood_notes', visit.mood_notes)
        visit.fp_counseled   = bool(p.get('fp_counseled'))
        visit.fp_method_chosen = p.get('fp_method_chosen', visit.fp_method_chosen)
        visit.fp_method_provided = bool(p.get('fp_method_provided'))
        visit.newborn_weight = p.get('newborn_weight') or visit.newborn_weight
        visit.newborn_condition = p.get('newborn_condition', visit.newborn_condition)
        visit.newborn_feeding   = p.get('newborn_feeding', visit.newborn_feeding)
        visit.chief_complaint= p.get('chief_complaint', visit.chief_complaint)
        visit.assessment     = p.get('assessment', visit.assessment)
        visit.plan           = p.get('plan', visit.plan)
        visit.prescribed_medicines = p.get('prescribed_medicines', visit.prescribed_medicines)
        visit.referral       = p.get('referral', visit.referral)
        visit.follow_up_date = p.get('follow_up_date') or visit.follow_up_date
        visit.notes          = p.get('notes', visit.notes)
        visit.save()
        messages.success(request, 'Postpartum visit updated.')
        return redirect('postpartum_detail', pk=pk)
    return render(request, 'postpartum/postpartum_form.html', {
        'visit': visit,
        'patients': patients,
        'deliveries': deliveries,
        'visit_types': PostpartumVisit.VISIT_TYPES,
        'breastfeeding_choices': PostpartumVisit.BREASTFEEDING,
        'fp_choices': PostpartumVisit.FP_METHODS,
        'today': timezone.now().date(),
    })


@login_required
@role_required('clinical')
def patient_postpartum(request, pk):
    """All postpartum visits for a specific patient."""
    patient = get_object_or_404(Patient, pk=pk)
    visits  = PostpartumVisit.objects.filter(
        patient=patient
    ).order_by('visit_date')
    return render(request, 'postpartum/patient_postpartum.html', {
        'patient': patient, 'visits': visits,
    })
