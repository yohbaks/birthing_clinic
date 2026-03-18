from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from accounts.permissions import role_required
from datetime import date
from .models import Appointment, QueueEntry
from patients.models import Patient

@login_required
@role_required('clinical')
def appointment_list(request):
    appts = Appointment.objects.select_related("patient").order_by("-date", "time")
    return render(request, "appointments/appointment_list.html",
                  {"appointments": appts, "today": date.today()})

@login_required
@role_required('clinical')
def appointment_add(request):
    patients = Patient.objects.filter(is_active=True).order_by("full_name")
    if request.method == "POST":
        p = request.POST
        patient = get_object_or_404(Patient, pk=p.get("patient"))
        appt = Appointment.objects.create(
            patient=patient,
            date=p.get("date"),
            time=p.get("time"),
            appointment_type=p.get("appointment_type", "prenatal"),
            assigned_staff=request.user,
            notes=p.get("notes", ""),
            status="confirmed",
        )
        messages.success(request, f"Appointment for {patient.full_name} on {appt.date} added.")
        return redirect("appointment_list")
    return render(request, "appointments/appointment_form.html", {"patients": patients})

@login_required
@role_required('clinical')
def appointment_edit(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    patients = Patient.objects.filter(is_active=True).order_by("full_name")
    if request.method == "POST":
        p = request.POST
        appt.patient_id  = p.get("patient", appt.patient_id)
        appt.date        = p.get("date", appt.date)
        appt.time        = p.get("time", appt.time)
        appt.appointment_type = p.get("appointment_type", appt.appointment_type)
        appt.notes       = p.get("notes", appt.notes)
        appt.status      = p.get("status", appt.status)
        appt.save()
        messages.success(request, "Appointment updated.")
        return redirect("appointment_list")
    return render(request, "appointments/appointment_form.html",
                  {"appt": appt, "patients": patients})

@login_required
@role_required('clinical')
def update_status(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        appt.status = request.POST.get("status", appt.status)
        appt.save()
    return redirect("appointment_list")

# ── QUEUE MANAGEMENT ────────────────────────────────────────────────────────────
@login_required
@role_required('clinical')
def queue_manage(request):
    """Full queue management page for staff."""
    today = date.today()
    today_queue = QueueEntry.objects.filter(queue_date=today).select_related(
        "patient", "appointment"
    ).order_by("queue_number")
    today_appts = Appointment.objects.filter(
        date=today, status__in=["confirmed", "pending"]
    ).select_related("patient").order_by("time")
    # Already queued patient IDs
    queued_ids = set(today_queue.values_list("patient_id", flat=True))
    # Next queue number
    last = today_queue.order_by("-queue_number").first()
    next_num = (last.queue_number + 1) if last else 1
    return render(request, "appointments/queue_manage.html", {
        "queue": today_queue,
        "today_appts": today_appts,
        "queued_ids": queued_ids,
        "next_num": next_num,
        "today": today,
    })

@login_required
@role_required('clinical')
def queue_add(request):
    """Add a patient to today's queue."""
    if request.method == "POST":
        today = date.today()
        patient_id = request.POST.get("patient")
        appt_id = request.POST.get("appointment") or None
        patient = get_object_or_404(Patient, pk=patient_id)
        # Get next queue number
        last = QueueEntry.objects.filter(queue_date=today).order_by("-queue_number").first()
        num = (last.queue_number + 1) if last else 1
        QueueEntry.objects.create(
            patient=patient,
            appointment_id=appt_id,
            queue_date=today,
            queue_number=num,
            status="waiting",
        )
        messages.success(request, f"#{num} — {patient.full_name} added to queue.")
    return redirect("queue_manage")

@login_required
@role_required('clinical')
def queue_update(request, pk):
    """Update queue entry status (call, done, skip)."""
    entry = get_object_or_404(QueueEntry, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "call":
            entry.status = "in_progress"
            entry.called_at = timezone.now()
        elif action == "done":
            entry.status = "done"
            entry.completed_at = timezone.now()
        elif action == "skip":
            entry.status = "skipped"
        elif action == "waiting":
            entry.status = "waiting"
            entry.called_at = None
        entry.save()
    return redirect("queue_manage")

@login_required
@role_required('clinical')
def queue_display(request):
    """Public-facing queue board (shown on screen in waiting area)."""
    today = date.today()
    queue = QueueEntry.objects.filter(queue_date=today).select_related(
        "patient"
    ).order_by("queue_number")
    now_serving = queue.filter(status="in_progress").first()
    next_up = queue.filter(status="waiting").first()
    return render(request, "appointments/queue_display.html", {
        "queue": queue,
        "now_serving": now_serving,
        "next_up": next_up,
        "today": today,
    })

@login_required
@role_required('clinical')
def queue_api(request):
    """JSON endpoint for live queue updates."""
    today = date.today()
    entries = QueueEntry.objects.filter(queue_date=today).select_related("patient").order_by("queue_number")
    data = [{
        "id": e.pk,
        "num": e.queue_number,
        "name": e.patient.full_name,
        "status": e.status,
    } for e in entries]
    return JsonResponse({"queue": data})

@login_required
@role_required('clinical')
def appointment_print_slip(request, pk):
    from django.http import HttpResponse
    appt = get_object_or_404(Appointment, pk=pk)
    # Simple HTML print slip
    from accounts.models import ClinicSettings
    cs = ClinicSettings.get()
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Appointment Slip — {appt.patient.full_name}</title>
<style>
  @media print {{ @page {{ margin: 1cm; }} }}
  body {{ font-family: Arial, sans-serif; max-width: 400px; margin: 0 auto; padding: 20px; color: #1A2B4B; }}
  .logo {{ text-align: center; margin-bottom: 8px; }}
  .clinic-name {{ font-size: 20px; font-weight: 900; color: #E8527A; text-align: center; }}
  .clinic-sub {{ font-size: 11px; color: #64748B; text-align: center; margin-bottom: 4px; }}
  .divider {{ border: none; border-top: 2px solid #E8527A; margin: 12px 0; }}
  .slip-title {{ text-align: center; font-size: 14px; font-weight: 800; color: #1A2B4B; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }}
  .row {{ display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #F0F4F8; font-size: 13px; }}
  .label {{ color: #64748B; font-weight: 600; }}
  .value {{ font-weight: 700; text-align: right; }}
  .appt-num {{ text-align: center; margin: 20px 0; }}
  .appt-num .date {{ font-size: 28px; font-weight: 900; color: #E8527A; }}
  .appt-num .time {{ font-size: 20px; font-weight: 700; color: #1A2B4B; }}
  .footer {{ text-align: center; font-size: 10px; color: #94A3B8; margin-top: 20px; }}
  .note {{ background: #FFF8F8; border: 1px solid #FFE4E8; border-radius: 8px; padding: 10px; font-size: 11px; color: #64748B; margin-top: 16px; }}
  .print-btn {{ display: block; margin: 16px auto; padding: 10px 24px; background: #E8527A; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 700; cursor: pointer; }}
  @media print {{ .print-btn {{ display: none; }} }}
</style>
</head>
<body>
<div class="logo"><img src="/static/img/logo.png" style="height:40px;filter:none;" alt="BirthCare"></div>
<div class="clinic-name">{cs.clinic_name}</div>
<div class="clinic-sub">{cs.clinic_tagline}</div>
{f'<div class="clinic-sub">{cs.address}</div>' if cs.address else ''}
{f'<div class="clinic-sub">{cs.contact_number}</div>' if cs.contact_number else ''}
<hr class="divider">
<div class="slip-title">Appointment Slip</div>

<div class="appt-num">
  <div class="date">{appt.date.strftime('%B %d, %Y')}</div>
  <div class="time">{appt.time.strftime('%I:%M %p') if appt.time else '—'}</div>
</div>

<div class="row"><span class="label">Patient Name</span><span class="value">{appt.patient.full_name}</span></div>
<div class="row"><span class="label">Record No.</span><span class="value">{appt.patient.record_number}</span></div>
<div class="row"><span class="label">Appointment Type</span><span class="value">{appt.get_appointment_type_display()}</span></div>
<div class="row"><span class="label">Status</span><span class="value">{appt.get_status_display()}</span></div>
{'<div class="row"><span class="label">Assigned Staff</span><span class="value">' + appt.assigned_staff.get_full_name() + '</span></div>' if appt.assigned_staff else ''}
{'<div class="row"><span class="label">Notes</span><span class="value" style="max-width:60%;text-align:right;">' + appt.notes + '</span></div>' if appt.notes else ''}

<div class="note">
  ⏰ Please arrive <strong>15 minutes early</strong> for your appointment.<br>
  Bring this slip and any previous medical records.<br>
  For rescheduling, please call us at least 24 hours in advance.
</div>

<div class="footer">
  Generated {appt.date.strftime('%B %d, %Y')} · {cs.clinic_name}
  {f'<br>PhilHealth Accreditation: {cs.philhealth_accno}' if cs.philhealth_accno else ''}
</div>

<button class="print-btn" onclick="window.print()">🖨️ Print Slip</button>
</body>
</html>"""
    return HttpResponse(html)
