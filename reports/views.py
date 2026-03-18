from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from accounts.permissions import role_required

@login_required
@role_required('patient_view')
def dashboard(request):
    from patients.models import Patient
    from appointments.models import Appointment
    from delivery.models import DeliveryRecord
    from newborn.models import NewbornRecord
    from inventory.models import InventoryItem
    from billing.models import Bill, Payment
    from prenatal.models import PrenatalVisit

    today = date.today()
    month_start = today.replace(day=1)

    # Stats
    total_patients = Patient.objects.filter(is_active=True).count()
    high_risk = Patient.objects.filter(risk_level='high', is_active=True).count()
    today_appointments = Appointment.objects.filter(date=today).exclude(status='cancelled').count()
    month_deliveries = DeliveryRecord.objects.filter(admission_datetime__date__gte=month_start).count()
    month_newborns = NewbornRecord.objects.filter(birth_datetime__date__gte=month_start).count()
    today_prenatal = PrenatalVisit.objects.filter(visit_date=today).count()
    unpaid_bills = Bill.objects.filter(payment_status__in=['unpaid','partial'], is_active=True).count()

    # Low stock
    low_stock_items = []
    try:
        from django.db.models import F
        low_stock_items = InventoryItem.objects.filter(
            is_active=True, quantity_on_hand__lte=F('reorder_level')
        )[:5]
    except: pass

    # Monthly income
    month_income = 0
    try:
        from django.db.models import Sum
        result = Payment.objects.filter(payment_date__date__gte=month_start).aggregate(Sum('amount'))
        month_income = result['amount__sum'] or 0
    except: pass

    # Recent activities
    recent_deliveries = DeliveryRecord.objects.select_related('patient').order_by('-admission_datetime')[:5]
    today_appt_list = Appointment.objects.filter(date=today).select_related('patient').exclude(status='cancelled').order_by('time')[:10]
    recent_patients = Patient.objects.filter(is_active=True).order_by('-created_at')[:5]

    # Chart data - monthly deliveries last 6 months
    months_data = []
    for i in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        next_month = (month_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        count = DeliveryRecord.objects.filter(
            admission_datetime__date__gte=month_date,
            admission_datetime__date__lt=next_month
        ).count()
        months_data.append({'month': month_date.strftime('%b %Y'), 'count': count})

    context = {
        'total_patients': total_patients,
        'high_risk': high_risk,
        'today_appointments': today_appointments,
        'month_deliveries': month_deliveries,
        'month_newborns': month_newborns,
        'today_prenatal': today_prenatal,
        'unpaid_bills': unpaid_bills,
        'low_stock_items': low_stock_items,
        'month_income': month_income,
        'recent_deliveries': recent_deliveries,
        'today_appt_list': today_appt_list,
        'recent_patients': recent_patients,
        'months_data': months_data,
        'today': today,
    }
    return render(request, 'reports/dashboard.html', context)

@login_required
def dashboard_stats_api(request):
    from patients.models import Patient
    from appointments.models import Appointment
    from delivery.models import DeliveryRecord
    from billing.models import Payment
    from django.db.models import Sum
    today = date.today()
    month_start = today.replace(day=1)
    stats = {
        'total_patients': Patient.objects.filter(is_active=True).count(),
        'today_appointments': Appointment.objects.filter(date=today).exclude(status='cancelled').count(),
        'month_deliveries': DeliveryRecord.objects.filter(admission_datetime__date__gte=month_start).count(),
        'month_income': float(Payment.objects.filter(payment_date__date__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or 0),
    }
    return JsonResponse(stats)

@login_required
@role_required('clinical')
def daily_census(request):
    from patients.models import Patient
    from appointments.models import Appointment
    from prenatal.models import PrenatalVisit
    target_date = request.GET.get('date', date.today().isoformat())
    try:
        target = date.fromisoformat(target_date)
    except:
        target = date.today()
    appointments = Appointment.objects.filter(date=target).select_related('patient')
    prenatal = PrenatalVisit.objects.filter(visit_date=target).select_related('patient')
    return render(request, 'reports/daily_census.html', {
        'appointments': appointments, 'prenatal': prenatal, 'target_date': target
    })

@login_required
@role_required('reports')
def delivery_report(request):
    from delivery.models import DeliveryRecord
    from django.db.models import Count
    month = request.GET.get('month', date.today().strftime('%Y-%m'))
    try:
        year, mo = map(int, month.split('-'))
        deliveries = DeliveryRecord.objects.filter(
            admission_datetime__year=year, admission_datetime__month=mo
        ).select_related('patient')
    except:
        deliveries = DeliveryRecord.objects.none()
    return render(request, 'reports/delivery_report.html', {
        'deliveries': deliveries, 'month': month
    })

@login_required
@role_required('billing_view')
def collection_report(request):
    from billing.models import Payment, Bill
    from django.db.models import Sum
    target_date = request.GET.get('date', date.today().isoformat())
    try:
        target = date.fromisoformat(target_date)
    except:
        target = date.today()
    payments = Payment.objects.filter(payment_date__date=target).select_related('bill__patient')
    total = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    return render(request, 'reports/collection_report.html', {
        'payments': payments, 'total': total, 'target_date': target
    })

from datetime import date, timedelta
from calendar import monthrange
from django.db.models import Count, Avg, Sum, Q
from accounts.permissions import role_required

@login_required
@role_required('reports')
def monthly_report(request):
    from patients.models import Patient
    from prenatal.models import PrenatalVisit
    from delivery.models import DeliveryRecord, DeliveryComplication
    from newborn.models import NewbornRecord
    from billing.models import Bill, Payment
    from appointments.models import Appointment

    # Determine reporting month/year
    today = date.today()
    year  = int(request.GET.get('year',  today.year))
    month = int(request.GET.get('month', today.month))
    first_day = date(year, month, 1)
    last_day  = date(year, month, monthrange(year, month)[1])

    # ── Patient registrations ──────────────────────────────
    new_patients = Patient.objects.filter(
        created_at__date__gte=first_day,
        created_at__date__lte=last_day
    )
    total_patients      = Patient.objects.filter(is_active=True).count()
    high_risk_patients  = Patient.objects.filter(risk_level='high', is_active=True).count()
    risk_breakdown = Patient.objects.filter(is_active=True).values('risk_level').annotate(n=Count('id'))

    # ── Prenatal visits ───────────────────────────────────
    prenatal_visits = PrenatalVisit.objects.filter(
        visit_date__gte=first_day, visit_date__lte=last_day
    )
    prenatal_count      = prenatal_visits.count()
    high_risk_visits    = prenatal_visits.filter(risk_flag='high_risk').count()
    avg_weight          = prenatal_visits.aggregate(a=Avg('weight'))['a']
    unique_patients_pn  = prenatal_visits.values('patient').distinct().count()

    # ── Appointments ──────────────────────────────────────
    appointments = Appointment.objects.filter(date__gte=first_day, date__lte=last_day)
    appt_total      = appointments.count()
    appt_completed  = appointments.filter(status='completed').count()
    appt_no_show    = appointments.filter(status='no_show').count()
    appt_cancelled  = appointments.filter(status='cancelled').count()
    appt_by_type    = appointments.values('appointment_type').annotate(n=Count('id')).order_by('-n')

    # ── Deliveries ────────────────────────────────────────
    deliveries = DeliveryRecord.objects.filter(
        admission_datetime__date__gte=first_day,
        admission_datetime__date__lte=last_day
    )
    del_total       = deliveries.count()
    del_nsd         = deliveries.filter(delivery_type='nsd').count()
    del_assisted    = deliveries.filter(delivery_type='assisted').count()
    del_cs          = deliveries.filter(delivery_type='cs').count()
    del_referral    = deliveries.filter(delivery_type='referral').count()
    del_in_progress = deliveries.filter(delivery_type='').count() + deliveries.filter(delivery_type__isnull=True).count()
    complications   = DeliveryComplication.objects.filter(
        delivery_record__in=deliveries
    ).values('complication_type').annotate(n=Count('id')).order_by('-n')

    # ── Newborns ──────────────────────────────────────────
    newborns = NewbornRecord.objects.filter(
        birth_datetime__date__gte=first_day,
        birth_datetime__date__lte=last_day
    )
    nb_total        = newborns.count()
    nb_alive        = newborns.filter(birth_status='alive').count()
    nb_stillbirth   = newborns.filter(birth_status='stillbirth').count()
    nb_male         = newborns.filter(gender='male').count()
    nb_female       = newborns.filter(gender='female').count()
    avg_weight_nb   = newborns.filter(birth_status='alive').aggregate(a=Avg('weight_grams'))['a']
    low_bw          = newborns.filter(birth_status='alive', weight_grams__lt=2500).count()

    # ── Billing / collections ─────────────────────────────
    bills_this_month    = Bill.objects.filter(
        billing_date__gte=first_day, billing_date__lte=last_day
    )
    total_billed        = bills_this_month.aggregate(s=Sum('total_amount'))['s'] or 0
    total_collected     = Payment.objects.filter(
        payment_date__date__gte=first_day,
        payment_date__date__lte=last_day
    ).aggregate(s=Sum('amount'))['s'] or 0
    bills_unpaid        = bills_this_month.filter(payment_status='unpaid').count()
    bills_partial       = bills_this_month.filter(payment_status='partial').count()
    bills_paid          = bills_this_month.filter(payment_status='paid').count()
    payment_by_method   = Payment.objects.filter(
        payment_date__date__gte=first_day,
        payment_date__date__lte=last_day
    ).values('payment_method').annotate(total=Sum('amount')).order_by('-total')

    # ── Month navigation ──────────────────────────────────
    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month = (last_day + timedelta(days=1)).replace(day=1)
    year_range = list(range(date.today().year - 3, date.today().year + 2))

    ctx = {
        'year': year, 'month': month,
        'month_name': first_day.strftime('%B %Y'),
        'first_day': first_day, 'last_day': last_day,
        'prev_month': prev_month, 'next_month': next_month,
        'year_range': year_range,
        # Patient
        'new_patients': new_patients.count(),
        'total_patients': total_patients,
        'high_risk_patients': high_risk_patients,
        'risk_breakdown': risk_breakdown,
        # Prenatal
        'prenatal_count': prenatal_count,
        'high_risk_visits': high_risk_visits,
        'avg_weight': round(avg_weight, 2) if avg_weight else None,
        'unique_patients_pn': unique_patients_pn,
        # Appointments
        'appt_total': appt_total, 'appt_completed': appt_completed,
        'appt_no_show': appt_no_show, 'appt_cancelled': appt_cancelled,
        'appt_by_type': appt_by_type,
        # Deliveries
        'del_total': del_total, 'del_nsd': del_nsd,
        'del_assisted': del_assisted, 'del_cs': del_cs,
        'del_referral': del_referral, 'del_in_progress': del_in_progress,
        'complications': complications,
        # Newborns
        'nb_total': nb_total, 'nb_alive': nb_alive,
        'nb_stillbirth': nb_stillbirth,
        'nb_male': nb_male, 'nb_female': nb_female,
        'avg_weight_nb': round(avg_weight_nb, 0) if avg_weight_nb else None,
        'low_bw': low_bw,
        # Billing
        'total_billed': total_billed, 'total_collected': total_collected,
        'bills_unpaid': bills_unpaid, 'bills_partial': bills_partial,
        'bills_paid': bills_paid, 'payment_by_method': payment_by_method,
    }
    return render(request, 'reports/monthly_report.html', ctx)


@login_required
@role_required('clinical')
def newborn_report(request):
    from newborn.models import NewbornRecord
    from django.db.models import Count, Avg, Min, Max

    today  = date.today()
    year   = int(request.GET.get('year', today.year))
    month  = int(request.GET.get('month', 0))  # 0 = full year

    qs = NewbornRecord.objects.select_related('mother', 'delivery_record').order_by('-birth_datetime')
    if month:
        first_day = date(year, month, 1)
        last_day  = date(year, month, monthrange(year, month)[1])
        qs = qs.filter(birth_datetime__date__gte=first_day, birth_datetime__date__lte=last_day)
        period_label = date(year, month, 1).strftime('%B %Y')
    else:
        qs = qs.filter(birth_datetime__year=year)
        period_label = str(year)

    total           = qs.count()
    alive           = qs.filter(birth_status='alive')
    alive_count     = alive.count()
    stillbirth      = qs.filter(birth_status='stillbirth').count()
    neonatal_death  = qs.filter(birth_status='neonatal_death').count()
    male            = qs.filter(gender='male').count()
    female          = qs.filter(gender='female').count()
    stats = alive.aggregate(
        avg_wt=Avg('weight_grams'),
        min_wt=Min('weight_grams'),
        max_wt=Max('weight_grams'),
        avg_len=Avg('length_cm'),
        avg_apgar1=Avg('apgar_1min'),
        avg_apgar5=Avg('apgar_5min'),
    )

    # Weight categories
    lbw        = alive.filter(weight_grams__lt=2500).count()
    normal_wt  = alive.filter(weight_grams__gte=2500, weight_grams__lt=4000).count()
    macrosomic = alive.filter(weight_grams__gte=4000).count()

    # APGAR distribution (alive only)
    apgar_low   = alive.filter(apgar_5min__lt=7).count()
    apgar_fair  = alive.filter(apgar_5min__gte=7, apgar_5min__lt=9).count()
    apgar_good  = alive.filter(apgar_5min__gte=9).count()

    # Interventions
    vit_k      = alive.filter(vitamin_k_given=True).count()
    eye_proph  = alive.filter(eye_prophylaxis_given=True).count()
    nbs_done   = alive.filter(newborn_screening_done=True).count()

    # Monthly breakdown for chart (only if showing full year)
    monthly_data = []
    if not month:
        for m in range(1, 13):
            m_qs = NewbornRecord.objects.filter(
                birth_datetime__year=year,
                birth_datetime__month=m
            )
            monthly_data.append({
                'month': date(year, m, 1).strftime('%b'),
                'total': m_qs.count(),
                'alive': m_qs.filter(birth_status='alive').count(),
                'male': m_qs.filter(gender='male').count(),
                'female': m_qs.filter(gender='female').count(),
            })

    year_range = list(range(date.today().year - 3, date.today().year + 2))

    ctx = {
        'year': year, 'month': month, 'period_label': period_label,
        'year_range': year_range, 'month_range': list(range(1, 13)),
        'total': total, 'alive_count': alive_count,
        'stillbirth': stillbirth, 'neonatal_death': neonatal_death,
        'male': male, 'female': female,
        'stats': stats,
        'lbw': lbw, 'normal_wt': normal_wt, 'macrosomic': macrosomic,
        'apgar_low': apgar_low, 'apgar_fair': apgar_fair, 'apgar_good': apgar_good,
        'vit_k': vit_k, 'eye_proph': eye_proph, 'nbs_done': nbs_done,
        'monthly_data': monthly_data,
        'newborns': qs[:50],
    }
    return render(request, 'reports/newborn_report.html', ctx)


@login_required
@role_required('reports')
def export_csv(request, model_type):
    """Export data as CSV for DOH and other reporting."""
    import csv
    from django.http import HttpResponse
    from datetime import date

    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="birthcare_{model_type}_{date.today()}.csv"'
    writer = csv.writer(response)

    if model_type == 'patients':
        from patients.models import Patient
        qs = Patient.objects.all().order_by('record_number')
        writer.writerow(['Record No', 'Full Name', 'Date of Birth', 'Age', 'Civil Status',
                          'Blood Type', 'Contact', 'Address', 'Risk Level',
                          'G', 'P', 'A', 'LMP', 'EDD', 'Registered'])
        for p in qs:
            writer.writerow([p.record_number, p.full_name, p.date_of_birth,
                              p.age, p.get_civil_status_display(), p.blood_type,
                              p.contact_number, p.address, p.get_risk_level_display(),
                              p.gravida, p.para, p.abortion_history,
                              p.lmp, p.edd, p.created_at.date()])

    elif model_type == 'deliveries':
        from delivery.models import DeliveryRecord
        qs = DeliveryRecord.objects.select_related('patient').order_by('-admission_datetime')
        if date_from: qs = qs.filter(admission_datetime__date__gte=date_from)
        if date_to:   qs = qs.filter(admission_datetime__date__lte=date_to)
        writer.writerow(['Patient Name', 'Record No', 'Admitted', 'Delivery Date',
                          'Delivery Type', 'Presentation', 'EBL (mL)',
                          'Complications', 'Maternal Condition', 'Midwife', 'Doctor'])
        for d in qs:
            writer.writerow([
                d.patient.full_name, d.patient.record_number,
                d.admission_datetime.strftime('%Y-%m-%d %H:%M') if d.admission_datetime else '',
                d.delivery_datetime.strftime('%Y-%m-%d %H:%M') if d.delivery_datetime else '',
                d.get_delivery_type_display() if d.delivery_type else '',
                d.presentation or '', d.estimated_blood_loss or '',
                d.complications or '', d.maternal_condition or '',
                d.attending_midwife.get_full_name() if d.attending_midwife else '',
                d.attending_doctor.get_full_name() if d.attending_doctor else '',
            ])

    elif model_type == 'newborns':
        from newborn.models import NewbornRecord
        qs = NewbornRecord.objects.select_related('mother').order_by('-birth_datetime')
        if date_from: qs = qs.filter(birth_datetime__date__gte=date_from)
        if date_to:   qs = qs.filter(birth_datetime__date__lte=date_to)
        writer.writerow(['Baby ID', 'Baby Name', 'Mother', 'Record No', 'Gender',
                          'Birth Date', 'Weight (g)', 'Length (cm)', 'Head Circ (cm)',
                          'APGAR 1min', 'APGAR 5min', 'Birth Status',
                          'Vit K', 'Eye Proph', 'NBS'])
        for nb in qs:
            writer.writerow([
                nb.baby_id, nb.baby_name or '', nb.mother.full_name,
                nb.mother.record_number, nb.get_gender_display(),
                nb.birth_datetime.strftime('%Y-%m-%d %H:%M') if nb.birth_datetime else '',
                nb.weight_grams, nb.length_cm, nb.head_circumference_cm or '',
                nb.apgar_1min or '', nb.apgar_5min or '',
                nb.get_birth_status_display(),
                'Yes' if nb.vitamin_k_given else 'No',
                'Yes' if nb.eye_prophylaxis_given else 'No',
                'Yes' if nb.newborn_screening_done else 'No',
            ])

    elif model_type == 'collections':
        from billing.models import Payment
        qs = Payment.objects.select_related('bill', 'bill__patient').order_by('-payment_date')
        if date_from: qs = qs.filter(payment_date__date__gte=date_from)
        if date_to:   qs = qs.filter(payment_date__date__lte=date_to)
        writer.writerow(['OR Number', 'Bill No', 'Patient', 'Date', 'Amount (₱)',
                          'Method', 'Reference', 'Received By'])
        for pay in qs:
            writer.writerow([
                pay.receipt_number, pay.bill.bill_number,
                pay.bill.patient.full_name,
                pay.payment_date.strftime('%Y-%m-%d %H:%M'),
                pay.amount, pay.get_payment_method_display(),
                pay.reference_number or '',
                pay.received_by.get_full_name() if pay.received_by else '',
            ])

    elif model_type == 'prenatal':
        from prenatal.models import PrenatalVisit
        qs = PrenatalVisit.objects.select_related('patient').order_by('-visit_date')
        if date_from: qs = qs.filter(visit_date__gte=date_from)
        if date_to:   qs = qs.filter(visit_date__lte=date_to)
        writer.writerow(['Visit Date', 'Patient', 'Record No', 'GA (wks)',
                          'Weight (kg)', 'BP', 'Temp', 'FHR', 'Fundal Ht', 'Risk Flag', 'Follow-up'])
        for v in qs:
            writer.writerow([
                v.visit_date, v.patient.full_name, v.patient.record_number,
                v.gestational_age_weeks, v.weight, v.bp_display,
                v.temperature, v.fetal_heart_rate or '',
                v.fundal_height or '', v.get_risk_flag_display(),
                v.follow_up_date or '',
            ])

    return response


@login_required
@role_required('reports')
def export_center(request):
    """Export center page — choose what to export."""
    return render(request, 'reports/export_center.html', {})

@login_required
@role_required('admin')
def system_health(request):
    """System health monitor page."""
    import os
    from django.conf import settings
    from django.contrib.sessions.models import Session
    from django.utils import timezone

    # DB size
    db_path = settings.DATABASES['default'].get('NAME', '')
    try:
        db_size_mb = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(str(db_path)) else 0
    except:
        db_size_mb = 0

    # Model counts
    from patients.models import Patient
    from prenatal.models import PrenatalVisit
    from delivery.models import DeliveryRecord
    from newborn.models import NewbornRecord
    from billing.models import Bill, Payment
    from inventory.models import InventoryItem, StockTransaction
    from appointments.models import Appointment
    from auditlogs.models import AuditLog
    from accounts.models import StaffProfile, LoginAttempt
    from datetime import timedelta

    model_counts = [
        ('Patients',         Patient.objects.count()),
        ('Prenatal Visits',  PrenatalVisit.objects.count()),
        ('Deliveries',       DeliveryRecord.objects.count()),
        ('Newborns',         NewbornRecord.objects.count()),
        ('Bills',            Bill.objects.count()),
        ('Payments',         Payment.objects.count()),
        ('Inventory Items',  InventoryItem.objects.count()),
        ('Stock Transactions', StockTransaction.objects.count()),
        ('Appointments',     Appointment.objects.count()),
        ('Audit Log Entries',AuditLog.objects.count()),
        ('Staff Accounts',   StaffProfile.objects.count()),
        ('Active Sessions',  Session.objects.count()),
    ]

    # Recent errors (failed logins)
    yesterday = timezone.now() - timedelta(hours=24)
    failed_logins_24h = LoginAttempt.objects.filter(
        attempted_at__gte=yesterday, success=False
    ).count()

    # Audit log activity
    audit_today = AuditLog.objects.filter(timestamp__date=timezone.now().date()).count()

    # Django version info
    import django
    import sys

    return render(request, 'reports/system_health.html', {
        'db_size_mb': round(db_size_mb, 2),
        'db_path': str(db_path),
        'model_counts': model_counts,
        'failed_logins_24h': failed_logins_24h,
        'audit_today': audit_today,
        'django_version': django.get_version(),
        'python_version': sys.version.split()[0],
        'debug_mode': settings.DEBUG,
        'timezone': settings.TIME_ZONE,
        'total_records': sum(c for _, c in model_counts),
    })


@login_required
@role_required('reports')
def fhsis_report(request):
    """
    DOH FHSIS M1 — Monthly Consolidation Report for Maternal and Child Health.
    Covers the standard indicators required for LGU reporting.
    """
    from datetime import date
    from django.db.models import Count, Q
    from patients.models import Patient
    from prenatal.models import PrenatalVisit
    from delivery.models import DeliveryRecord, DeliveryComplication
    from newborn.models import NewbornRecord
    from billing.models import Payment
    from postpartum.models import PostpartumVisit

    today  = date.today()
    year   = int(request.GET.get('year',  today.year))
    month  = int(request.GET.get('month', today.month))
    from calendar import monthrange
    from datetime import timedelta
    first_day = date(year, month, 1)
    last_day  = date(year, month, monthrange(year, month)[1])

    # ── PRENATAL CARE ──────────────────────────────────────
    pn_visits = PrenatalVisit.objects.filter(
        visit_date__range=[first_day, last_day]
    )
    pn_new_registrants = Patient.objects.filter(
        created_at__date__range=[first_day, last_day]
    ).count()
    pn_first_trimester = pn_visits.filter(gestational_age_weeks__lte=12).values(
        'patient'
    ).distinct().count()
    pn_4plus_visits = (
        Patient.objects
        .annotate(visit_count=Count('prenatal_visits',
                                    filter=Q(prenatal_visits__visit_date__range=[
                                        date(year, 1, 1), last_day])))
        .filter(visit_count__gte=4).count()
    )
    pn_high_risk = pn_visits.filter(risk_flag='high_risk').values(
        'patient').distinct().count()
    pn_with_iron = pn_visits.filter(
        prescribed_medicines__icontains='ferrous'
    ).values('patient').distinct().count()
    pn_with_folic = pn_visits.filter(
        prescribed_medicines__icontains='folic'
    ).values('patient').distinct().count()
    pn_with_tt = Patient.objects.filter(
        maternal_immunizations__date_given__range=[first_day, last_day],
        maternal_immunizations__vaccine__in=['tt1','tt2','tt3','tt4','tt5']
    ).distinct().count()

    # ── DELIVERY ───────────────────────────────────────────
    deliveries = DeliveryRecord.objects.filter(
        admission_datetime__date__range=[first_day, last_day]
    )
    del_total      = deliveries.count()
    del_livebirths = NewbornRecord.objects.filter(
        birth_datetime__date__range=[first_day, last_day],
        birth_status='alive'
    ).count()
    del_stillbirths = NewbornRecord.objects.filter(
        birth_datetime__date__range=[first_day, last_day],
        birth_status='stillbirth'
    ).count()
    del_nsd   = deliveries.filter(delivery_type='nsd').count()
    del_cs    = deliveries.filter(delivery_type='cs').count()
    del_compl = DeliveryComplication.objects.filter(
        delivery_record__in=deliveries
    ).count()
    del_referral = deliveries.filter(delivery_type='referral').count()
    del_maternal_deaths = deliveries.filter(
        maternal_condition__icontains='death'
    ).count() + deliveries.filter(maternal_condition__icontains='expired').count()

    # ── NEWBORN ────────────────────────────────────────────
    newborns = NewbornRecord.objects.filter(
        birth_datetime__date__range=[first_day, last_day],
        birth_status='alive'
    )
    nb_total      = newborns.count()
    nb_low_bw     = newborns.filter(weight_grams__lt=2500).count()
    nb_normal_bw  = newborns.filter(weight_grams__range=[2500,3999]).count()
    nb_vit_k      = newborns.filter(vitamin_k_given=True).count()
    nb_eye_proph  = newborns.filter(eye_prophylaxis_given=True).count()
    nb_nbs        = newborns.filter(newborn_screening_done=True).count()
    nb_deaths     = NewbornRecord.objects.filter(
        birth_datetime__date__range=[first_day, last_day],
        birth_status='neonatal_death'
    ).count()

    # ── POSTPARTUM ─────────────────────────────────────────
    pp_visits  = PostpartumVisit.objects.filter(
        visit_date__range=[first_day, last_day]
    )
    pp_total   = pp_visits.count()
    pp_6week   = pp_visits.filter(visit_type='6week').count()
    pp_bf_excl = pp_visits.filter(breastfeeding='exclusive').count()
    pp_fp_counseled = pp_visits.filter(fp_counseled=True).values(
        'patient').distinct().count()
    pp_fp_methods = pp_visits.filter(
        fp_method_chosen__in=['pills','injectable','iud','implant','btl','condom','minipill']
    ).exclude(fp_method_chosen='none').count()
    pp_depression = pp_visits.filter(mood_score__gte=10).count()

    year_range  = list(range(date.today().year - 3, date.today().year + 2))
    month_names = ['','January','February','March','April','May','June',
                   'July','August','September','October','November','December']

    ctx = {
        'year': year, 'month': month,
        'month_name': f"{month_names[month]} {year}",
        'first_day': first_day, 'last_day': last_day,
        'year_range': year_range, 'month_range': range(1, 13),
        'month_names': month_names,
        # Prenatal
        'pn_new_registrants': pn_new_registrants,
        'pn_first_trimester': pn_first_trimester,
        'pn_4plus_visits': pn_4plus_visits,
        'pn_high_risk': pn_high_risk,
        'pn_with_iron': pn_with_iron,
        'pn_with_folic': pn_with_folic,
        'pn_with_tt': pn_with_tt,
        'pn_total_visits': pn_visits.count(),
        # Delivery
        'del_total': del_total,
        'del_livebirths': del_livebirths,
        'del_stillbirths': del_stillbirths,
        'del_nsd': del_nsd,
        'del_cs': del_cs,
        'del_compl': del_compl,
        'del_referral': del_referral,
        'del_maternal_deaths': del_maternal_deaths,
        # Newborn
        'nb_total': nb_total,
        'nb_low_bw': nb_low_bw,
        'nb_normal_bw': nb_normal_bw,
        'nb_vit_k': nb_vit_k,
        'nb_eye_proph': nb_eye_proph,
        'nb_nbs': nb_nbs,
        'nb_deaths': nb_deaths,
        # Postpartum
        'pp_total': pp_total,
        'pp_6week': pp_6week,
        'pp_bf_excl': pp_bf_excl,
        'pp_fp_counseled': pp_fp_counseled,
        'pp_fp_methods': pp_fp_methods,
        'pp_depression': pp_depression,
    }
    return render(request, 'reports/fhsis_report.html', ctx)


@login_required
@role_required('reports')
def morbidity_report(request):
    """Maternal Morbidity & Mortality Report — tracks adverse outcomes."""
    from datetime import date
    from django.db.models import Count
    from delivery.models import DeliveryRecord, DeliveryComplication, LaborMonitoring

    today = date.today()
    year  = int(request.GET.get('year', today.year))

    # All deliveries this year
    deliveries = DeliveryRecord.objects.filter(
        admission_datetime__year=year
    ).select_related('patient')

    complications = DeliveryComplication.objects.filter(
        delivery_record__admission_datetime__year=year
    ).select_related('delivery_record__patient').order_by('-recorded_at')

    # Complication type breakdown
    comp_breakdown = complications.values(
        'complication_type'
    ).annotate(count=Count('id')).order_by('-count')

    # High BP cases (pre-eclampsia/eclampsia)
    high_bp_deliveries = deliveries.filter(
        patient__prenatal_visits__risk_flag='high_risk'
    ).distinct()

    # Referrals
    referrals = deliveries.filter(
        delivery_type='referral'
    ).select_related('patient')

    # Maternal deaths (text search)
    maternal_deaths = deliveries.filter(
        maternal_condition__icontains='death'
    ) | deliveries.filter(maternal_condition__icontains='expired')

    # Neonatal deaths
    from newborn.models import NewbornRecord
    neonatal_deaths = NewbornRecord.objects.filter(
        birth_datetime__year=year,
        birth_status='neonatal_death'
    ).select_related('mother')

    stillbirths = NewbornRecord.objects.filter(
        birth_datetime__year=year,
        birth_status='stillbirth'
    ).select_related('mother')

    # Monthly trend for chart
    monthly_comp = []
    for m in range(1, 13):
        mcomps = DeliveryComplication.objects.filter(
            delivery_record__admission_datetime__year=year,
            delivery_record__admission_datetime__month=m
        ).count()
        mdels  = DeliveryRecord.objects.filter(
            admission_datetime__year=year,
            admission_datetime__month=m
        ).count()
        monthly_comp.append({
            'month': date(year, m, 1).strftime('%b'),
            'deliveries': mdels,
            'complications': mcomps,
        })

    import json
    year_range = list(range(date.today().year - 4, date.today().year + 2))

    ctx = {
        'year': year,
        'year_range': year_range,
        'total_deliveries': deliveries.count(),
        'total_complications': complications.count(),
        'comp_breakdown': comp_breakdown,
        'complications': complications[:50],
        'high_bp_count': high_bp_deliveries.count(),
        'referrals': referrals,
        'referral_count': referrals.count(),
        'maternal_deaths': maternal_deaths.count(),
        'neonatal_deaths': neonatal_deaths,
        'neonatal_death_count': neonatal_deaths.count(),
        'stillbirths': stillbirths,
        'stillbirth_count': stillbirths.count(),
        'monthly_comp': json.dumps(monthly_comp),
        'complication_rate': round(
            (complications.count() / deliveries.count() * 100), 1
        ) if deliveries.count() > 0 else 0,
    }
    return render(request, 'reports/morbidity_report.html', ctx)
