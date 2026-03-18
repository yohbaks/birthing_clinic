from django.utils import timezone
from datetime import date

def clinic_alerts(request):
    if not request.user.is_authenticated:
        return {}
    context = {}
    try:
        from inventory.models import InventoryItem
        from billing.models import Bill
        from appointments.models import Appointment
        from patients.models import Patient

        today = date.today()
        low_stock_count = InventoryItem.objects.filter(
            quantity_on_hand__lte=models_reorder(), is_active=True
        ).count() if False else 0

        try:
            low_stock_count = InventoryItem.objects.filter(
                is_active=True
            ).extra(where=['quantity_on_hand <= reorder_level']).count()
        except:
            low_stock_count = InventoryItem.objects.filter(
                quantity_on_hand__lte=0, is_active=True
            ).count()

        unpaid_count = Bill.objects.filter(payment_status__in=['unpaid', 'partial']).count()
        today_appt = Appointment.objects.filter(date=today, status='confirmed').count()
        high_risk_count = Patient.objects.filter(risk_level='high', is_active=True).count()

        context = {
            'alert_low_stock': low_stock_count,
            'alert_unpaid_bills': unpaid_count,
            'alert_today_appointments': today_appt,
            'alert_high_risk': high_risk_count,
        }
    except Exception:
        context = {
            'alert_low_stock': 0,
            'alert_unpaid_bills': 0,
            'alert_today_appointments': 0,
            'alert_high_risk': 0,
        }
    return context


def user_permissions(request):
    """Inject role and permission flags into every template context."""
    if not request.user.is_authenticated:
        return {}
    try:
        from accounts.permissions import user_has_permission, get_user_role
        role = get_user_role(request.user)
        return {
            'user_role': role,
            'user_role_display': (role or '').replace('_', ' ').title(),
            'can_clinical':   user_has_permission(request.user, 'clinical'),
            'can_clinical_staff': user_has_permission(request.user, 'clinical_staff'),
            'can_delivery':   user_has_permission(request.user, 'delivery'),
            'can_billing':    user_has_permission(request.user, 'billing'),
            'can_billing_view': user_has_permission(request.user, 'billing_view'),
            'can_inventory':  user_has_permission(request.user, 'inventory'),
            'can_reports':    user_has_permission(request.user, 'reports'),
            'can_admin':      user_has_permission(request.user, 'admin'),
            'can_patient_view': user_has_permission(request.user, 'patient_view'),
            'can_staff_mgmt': user_has_permission(request.user, 'staff_mgmt'),
        }
    except Exception:
        return {}
