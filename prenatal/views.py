from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.permissions import role_required
from .models import PrenatalVisit, LabRequest, UltrasoundRecord
from patients.models import Patient

@login_required
@role_required('clinical')
def prenatal_list(request):
    visits = PrenatalVisit.objects.select_related('patient').order_by('-visit_date')
    return render(request, 'prenatal/prenatal_list.html', {'visits': visits})

@login_required
@role_required('clinical_staff')
def prenatal_add(request):
    patients = Patient.objects.filter(is_active=True).order_by('full_name')
    if request.method == 'POST':
        p = request.POST
        patient = get_object_or_404(Patient, pk=p.get('patient'))
        visit = PrenatalVisit.objects.create(
            patient=patient,
            visit_date=p.get('visit_date'),
            gestational_age_weeks=p.get('gestational_age_weeks'),
            weight=p.get('weight'),
            blood_pressure_systolic=p.get('bp_systolic'),
            blood_pressure_diastolic=p.get('bp_diastolic'),
            temperature=p.get('temperature', 36.5),
            fetal_heart_rate=p.get('fetal_heart_rate') or None,
            fundal_height=p.get('fundal_height') or None,
            chief_complaint=p.get('chief_complaint', ''),
            assessment=p.get('assessment', ''),
            plan=p.get('plan', ''),
            prescribed_medicines=p.get('prescribed_medicines', ''),
            follow_up_date=p.get('follow_up_date') or None,
            risk_flag=p.get('risk_flag', 'normal'),
            notes=p.get('notes', ''),
            attending_staff=request.user,
        )
        messages.success(request, f'Prenatal visit for {patient.full_name} recorded.')
        return redirect('prenatal_detail', pk=visit.pk)
    import json
    patient_lmps = {}
    for p in patients:
        if p.lmp:
            patient_lmps[str(p.pk)] = str(p.lmp)
    return render(request, 'prenatal/prenatal_form.html', {
        'patients': patients,
        'patient_lmps': json.dumps(patient_lmps),
    })

@login_required
@role_required('clinical')
def prenatal_detail(request, pk):
    visit = get_object_or_404(PrenatalVisit, pk=pk)
    lab_requests = visit.lab_requests.all()
    return render(request, 'prenatal/prenatal_detail.html', {
        'visit': visit,
        'lab_requests': lab_requests,
    })

@login_required
@role_required('clinical_staff')
def prenatal_edit(request, pk):
    visit = get_object_or_404(PrenatalVisit, pk=pk)
    patients = Patient.objects.filter(is_active=True).order_by('full_name')
    if request.method == 'POST':
        p = request.POST
        visit.visit_date = p.get('visit_date', visit.visit_date)
        visit.gestational_age_weeks = p.get('gestational_age_weeks', visit.gestational_age_weeks)
        visit.weight = p.get('weight', visit.weight)
        visit.blood_pressure_systolic = p.get('bp_systolic', visit.blood_pressure_systolic)
        visit.blood_pressure_diastolic = p.get('bp_diastolic', visit.blood_pressure_diastolic)
        visit.temperature = p.get('temperature', visit.temperature)
        visit.fetal_heart_rate = p.get('fetal_heart_rate') or visit.fetal_heart_rate
        visit.fundal_height = p.get('fundal_height') or visit.fundal_height
        visit.chief_complaint = p.get('chief_complaint', visit.chief_complaint)
        visit.assessment = p.get('assessment', visit.assessment)
        visit.plan = p.get('plan', visit.plan)
        visit.prescribed_medicines = p.get('prescribed_medicines', visit.prescribed_medicines)
        visit.follow_up_date = p.get('follow_up_date') or visit.follow_up_date
        visit.risk_flag = p.get('risk_flag', visit.risk_flag)
        visit.notes = p.get('notes', visit.notes)
        visit.save()
        messages.success(request, 'Prenatal visit updated.')
        return redirect('prenatal_detail', pk=pk)
    import json
    patient_lmps = {}
    for p in patients:
        if p.lmp:
            patient_lmps[str(p.pk)] = str(p.lmp)
    return render(request, 'prenatal/prenatal_form.html', {
        'patients': patients, 'visit': visit,
        'patient_lmps': json.dumps(patient_lmps),
    })

@login_required
@role_required('clinical_staff')
def add_lab_request(request, pk):
    visit = get_object_or_404(PrenatalVisit, pk=pk)
    if request.method == 'POST':
        p = request.POST
        LabRequest.objects.create(
            visit=visit,
            test_name=p.get('test_name', ''),
            result=p.get('result', ''),
            result_date=p.get('result_date') or None,
            notes=p.get('notes', ''),
        )
        messages.success(request, 'Lab request added.')
    return redirect('prenatal_detail', pk=pk)

@login_required
@role_required('clinical_staff')
def add_ultrasound(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    visits = patient.prenatal_visits.order_by('-visit_date')
    if request.method == 'POST':
        p = request.POST
        visit_pk = p.get('visit')
        UltrasoundRecord.objects.create(
            patient=patient,
            visit_id=visit_pk or None,
            date=p.get('date'),
            findings=p.get('findings', ''),
            ga_by_ultrasound=p.get('ga_by_ultrasound') or None,
            done_by=p.get('done_by', ''),
            notes=p.get('notes', ''),
        )
        messages.success(request, 'Ultrasound record added.')
        return redirect('patient_profile', pk=patient_pk)
    return render(request, 'prenatal/ultrasound_form.html', {'patient': patient, 'visits': visits})

@login_required
@role_required('patient_view')
def patient_prenatal(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    visits = patient.prenatal_visits.all()
    ultrasounds = patient.ultrasounds.all().order_by('-date')
    return render(request, 'prenatal/patient_prenatal.html', {
        'patient': patient, 'visits': visits, 'ultrasounds': ultrasounds,
    })
