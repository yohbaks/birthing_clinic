from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from accounts.permissions import role_required
from .models import StaffProfile
from auditlogs.middleware import log_action

def login_view(request):
    from .models import LoginAttempt, ActiveSession
    from django.utils import timezone
    from datetime import timedelta

    MAX_ATTEMPTS   = 5
    LOCKOUT_MINUTES= 15

    if request.user.is_authenticated:
        return redirect('dashboard')

    ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    lockout_since = timezone.now() - timedelta(minutes=LOCKOUT_MINUTES)
    recent_fails  = LoginAttempt.objects.filter(
        ip_address=ip, success=False, attempted_at__gte=lockout_since
    ).count()
    locked_out = recent_fails >= MAX_ATTEMPTS

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        if locked_out:
            messages.error(request, f'Too many failed attempts. Please wait {LOCKOUT_MINUTES} minutes and try again.')
            return render(request, 'accounts/login.html', {'locked_out': True})

        user = authenticate(request, username=username, password=password)
        # Always record the attempt
        LoginAttempt.objects.create(
            ip_address=ip, username=username, success=bool(user)
        )
        if user:
            if not user.is_active:
                messages.error(request, 'This account has been deactivated. Contact your administrator.')
                return render(request, 'accounts/login.html')
            login(request, user)
            # Track active session
            try:
                if not request.session.session_key:
                    request.session.create()
                ActiveSession.objects.update_or_create(
                    session_key=request.session.session_key,
                    defaults={
                        'user': user,
                        'ip_address': ip,
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                    }
                )
            except Exception:
                pass
            log_action(user, 'login', 'Auth', user.pk,
                       f'Successful login from {ip}')
            return redirect('dashboard')
        else:
            remaining = MAX_ATTEMPTS - recent_fails - 1
            if remaining <= 0:
                messages.error(request, f'Account locked for {LOCKOUT_MINUTES} minutes due to too many failed attempts.')
            else:
                messages.error(request, f'Invalid username or password. {remaining} attempt(s) remaining before lockout.')

    return render(request, 'accounts/login.html', {'locked_out': locked_out})


def logout_view(request):
    if request.user.is_authenticated:
        log_action(request.user, 'logout', 'Auth', request.user.pk, 'User logged out')
    logout(request)
    return redirect('login')

@login_required
@role_required('staff_mgmt')
def staff_list(request):
    staff = StaffProfile.objects.select_related('user').filter(is_active=True).order_by('user__last_name')
    return render(request, 'accounts/staff_list.html', {'staff': staff})

@login_required
@role_required('staff_mgmt')
def staff_add(request):
    if request.method == 'POST':
        p = request.POST
        if User.objects.filter(username=p.get('username')).exists():
            messages.error(request, f'Username "{p.get("username")}" already exists.')
            return render(request, 'accounts/staff_form.html')
        user = User.objects.create_user(
            username=p.get('username'),
            password=p.get('password'),
            first_name=p.get('first_name'),
            last_name=p.get('last_name'),
            email=p.get('email', ''),
        )
        StaffProfile.objects.create(
            user=user,
            role=p.get('role', 'receptionist'),
            phone=p.get('phone', ''),
            license_number=p.get('license_number', ''),
        )
        messages.success(request, f'Staff account created for {user.get_full_name()}.')
        return redirect('staff_list')
    return render(request, 'accounts/staff_form.html')

@login_required
@role_required('staff_mgmt')
def staff_edit(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    if request.method == 'POST':
        p = request.POST
        profile.user.first_name = p.get('first_name', profile.user.first_name)
        profile.user.last_name = p.get('last_name', profile.user.last_name)
        profile.user.email = p.get('email', profile.user.email)
        profile.user.save()
        profile.role = p.get('role', profile.role)
        profile.phone = p.get('phone', profile.phone)
        profile.license_number = p.get('license_number', profile.license_number)
        profile.save()
        messages.success(request, 'Staff profile updated.')
        return redirect('staff_list')
    return render(request, 'accounts/staff_form.html', {'profile': profile})

@login_required
def my_profile(request):
    try:
        profile = request.user.staff_profile
    except:
        profile = None
    return render(request, 'accounts/my_profile.html', {'profile': profile})

@login_required
def change_password(request):
    if request.method == 'POST':
        p = request.POST
        old_pw = p.get('old_password', '')
        new_pw = p.get('new_password', '')
        confirm_pw = p.get('confirm_password', '')
        if not request.user.check_password(old_pw):
            messages.error(request, 'Current password is incorrect.')
        elif new_pw != confirm_pw:
            messages.error(request, 'New passwords do not match.')
        elif len(new_pw) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new_pw)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('my_profile')
    return render(request, 'accounts/change_password.html')

@login_required
@role_required('staff_mgmt')
def staff_deactivate(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    if profile.user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('staff_list')
    if request.method == 'POST':
        profile.is_active = False
        profile.user.is_active = False
        profile.user.save()
        profile.save()
        messages.success(request, f'{profile.user.get_full_name()} account deactivated.')
        return redirect('staff_list')
    return render(request, 'accounts/staff_confirm_deactivate.html', {'profile': profile})

@login_required
@role_required('staff_mgmt')
def staff_reactivate(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    if request.method == 'POST':
        profile.is_active = True
        profile.user.is_active = True
        profile.user.save()
        profile.save()
        messages.success(request, f'{profile.user.get_full_name()} account reactivated.')
        return redirect('staff_list')
    return redirect('staff_list')

@login_required
@role_required('admin')
def clinic_settings(request):
    from .models import ClinicSettings
    settings = ClinicSettings.get()
    if request.method == 'POST':
        p = request.POST
        settings.clinic_name       = p.get('clinic_name', settings.clinic_name)
        settings.clinic_tagline    = p.get('clinic_tagline', settings.clinic_tagline)
        settings.address           = p.get('address', settings.address)
        settings.contact_number    = p.get('contact_number', settings.contact_number)
        settings.email             = p.get('email', settings.email)
        settings.philhealth_accno  = p.get('philhealth_accno', settings.philhealth_accno)
        settings.doh_license       = p.get('doh_license', settings.doh_license)
        settings.head_physician    = p.get('head_physician', settings.head_physician)
        settings.head_midwife      = p.get('head_midwife', settings.head_midwife)
        settings.default_delivery_fee = p.get('default_delivery_fee', 0) or 0
        settings.default_room_rate    = p.get('default_room_rate', 0) or 0
        settings.save()
        messages.success(request, 'Clinic settings updated successfully.')
        return redirect('clinic_settings')
    return render(request, 'accounts/clinic_settings.html', {'settings': settings})

@login_required
@role_required('admin')
def session_monitor(request):
    """Active session management for admins."""
    from .models import ActiveSession, LoginAttempt
    from django.utils import timezone
    from datetime import timedelta
    # Clean stale sessions (older than 8 hours)
    stale = timezone.now() - timedelta(hours=8)
    ActiveSession.objects.filter(last_activity__lt=stale).delete()
    sessions = ActiveSession.objects.select_related('user').order_by('-last_activity')
    # Recent login attempts (last 24h)
    yesterday = timezone.now() - timedelta(hours=24)
    recent_attempts = LoginAttempt.objects.filter(
        attempted_at__gte=yesterday
    ).order_by('-attempted_at')[:100]
    failed_ips = LoginAttempt.objects.filter(
        attempted_at__gte=timezone.now()-timedelta(minutes=15),
        success=False
    ).values('ip_address').annotate(
        count=__import__('django.db.models',fromlist=['Count']).Count('id')
    ).filter(count__gte=3)
    return render(request, 'accounts/session_monitor.html', {
        'sessions': sessions,
        'recent_attempts': recent_attempts,
        'failed_ips': failed_ips,
    })

@login_required
@role_required('clinical')
def send_appointment_reminder(request, pk):
    """Manually send a reminder email for a specific appointment."""
    from appointments.models import Appointment
    from accounts.models import ClinicSettings
    from django.core.mail import send_mail
    appt = get_object_or_404(Appointment, pk=pk)
    cs = ClinicSettings.get()
    email = getattr(appt.patient, 'email', None)
    if not email:
        messages.warning(request, f'No email address on file for {appt.patient.full_name}.')
        return redirect('appointment_list')
    try:
        send_mail(
            subject=f'Appointment Reminder — {cs.clinic_name}',
            message=f"Dear {appt.patient.full_name}, your appointment is on {appt.date} at {appt.time or 'TBD'}. Please arrive 15 minutes early. — {cs.clinic_name}",
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )
        messages.success(request, f'Reminder sent to {email}.')
    except Exception as e:
        messages.error(request, f'Could not send email: {e}')
    return redirect('appointment_list')
