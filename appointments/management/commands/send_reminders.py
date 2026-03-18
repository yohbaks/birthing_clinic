"""
Management command to send appointment reminders.
Usage: python manage.py send_reminders
Schedule with cron: 0 8 * * * /path/to/venv/bin/python manage.py send_reminders
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Send appointment reminders for tomorrow's appointments'

    def handle(self, *args, **kwargs):
        from appointments.models import Appointment
        from accounts.models import ClinicSettings
        cs = ClinicSettings.get()
        tomorrow = date.today() + timedelta(days=1)
        appts = Appointment.objects.filter(
            date=tomorrow, status__in=['confirmed', 'pending']
        ).select_related('patient')

        sent = skipped = 0
        for appt in appts:
            email = getattr(appt.patient, 'email', None)
            if not email:
                skipped += 1
                continue
            try:
                send_mail(
                    subject=f'Appointment Reminder — {cs.clinic_name}',
                    message=f"""Dear {appt.patient.full_name},

This is a reminder that you have an appointment tomorrow:

Date: {appt.date.strftime("%B %d, %Y")}
Time: {appt.time.strftime("%I:%M %p") if appt.time else "Please call to confirm"}
Type: {appt.get_appointment_type_display()}

Please arrive 15 minutes early.
Bring this confirmation and any previous medical records.

If you need to reschedule, please contact us at {cs.contact_number}.

{cs.clinic_name}
{cs.address}
""",
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=False,
                )
                sent += 1
            except Exception as e:
                self.stderr.write(f"Failed to send to {email}: {e}")
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(f"Reminders: {sent} sent, {skipped} skipped (no email or error)")
        )
