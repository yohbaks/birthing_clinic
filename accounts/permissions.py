"""
Role-Based Access Control for BirthCare Clinic.

Usage in views:
    from accounts.permissions import role_required, get_user_role

    @login_required
    @role_required('clinical')      # any clinical staff
    def prenatal_add(request): ...

    @login_required
    @role_required('billing')       # cashier / admin
    def bill_add(request): ...

    @login_required
    @role_required('admin')         # admin / super_admin only
    def staff_add(request): ...
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden

# ── Permission Groups ──────────────────────────────────────────────────────────
# Map group name → list of allowed roles
PERMISSION_GROUPS = {
    # Full access
    'admin':      ['super_admin', 'admin'],

    # Can view/manage patient clinical records
    'clinical':   ['super_admin', 'admin', 'doctor', 'midwife', 'nurse', 'receptionist'],

    # Can view patient list and profiles (for billing lookup)
    'patient_view': ['super_admin', 'admin', 'doctor', 'midwife', 'nurse', 'receptionist', 'cashier'],

    # Can do clinical procedures (not receptionist)
    'clinical_staff': ['super_admin', 'admin', 'doctor', 'midwife', 'nurse'],

    # Can manage deliveries & newborn
    'delivery':   ['super_admin', 'admin', 'doctor', 'midwife', 'nurse'],

    # Can manage billing
    'billing':    ['super_admin', 'admin', 'cashier'],

    # Can view billing (wider access to read)
    'billing_view': ['super_admin', 'admin', 'cashier', 'doctor', 'midwife', 'nurse'],

    # Can manage inventory
    'inventory':  ['super_admin', 'admin', 'inventory_clerk'],

    # Can view reports
    'reports':    ['super_admin', 'admin', 'doctor', 'midwife', 'cashier'],

    # Can manage staff
    'staff_mgmt': ['super_admin', 'admin'],
}

# ── URL-to-group mapping ───────────────────────────────────────────────────────
# Maps URL name patterns → required permission group
URL_PERMISSIONS = {
    # Dashboard
    'dashboard':            'clinical',
    'dashboard_stats_api':  'clinical',
    'daily_census':         'clinical',
    'delivery_report':      'reports',
    'collection_report':    'billing_view',
    'monthly_report':       'reports',
    'newborn_report':       'clinical',

    # Patients
    'patient_list':         'clinical',
    'patient_add':          'clinical',
    'patient_profile':      'clinical',
    'patient_edit':         'clinical',
    'patient_prenatal':     'patient_view',
    'deactivate_patient':   'admin',
    'reactivate_patient':   'admin',
    'inactive_patients':    'admin',
    'add_pregnancy_history':'clinical',

    # Prenatal
    'prenatal_list':        'clinical',
    'prenatal_add':         'clinical_staff',
    'prenatal_detail':      'clinical',
    'prenatal_edit':        'clinical_staff',
    'add_lab_request':      'clinical_staff',
    'add_ultrasound':       'clinical_staff',

    # Appointments
    'appointment_list':     'clinical',
    'appointment_add':      'clinical',
    'appointment_edit':     'clinical',
    'appointment_status':   'clinical',
    'queue_manage':         'clinical',
    'queue_add':            'clinical',
    'queue_update':         'clinical',
    'queue_display':        'clinical',
    'queue_api':            'clinical',

    # Delivery
    'delivery_list':        'clinical',
    'delivery_admit':       'delivery',
    'delivery_detail':      'clinical',
    'labor_monitor':        'clinical',
    'add_monitoring':       'delivery',
    'add_complication':     'delivery',

    # Newborn
    'newborn_list':         'clinical',
    'newborn_add':          'delivery',
    'newborn_detail':       'clinical',
    'newborn_edit':         'delivery',
    'add_immunization':     'delivery',
    'discharge_newborn':    'delivery',

    # Inventory
    'inventory_list':       'inventory',
    'item_add':             'inventory',
    'item_detail':          'inventory',
    'item_edit':            'inventory',
    'stock_in':             'inventory',
    'stock_out':            'inventory',
    'low_stock':            'inventory',
    'expiry_report':        'inventory',
    'supplier_list':        'inventory',
    'supplier_add':         'inventory',
    'supplier_detail':      'inventory',
    'supplier_edit':        'inventory',
    'po_list':              'inventory',
    'po_add':               'inventory',
    'po_detail':            'inventory',
    'po_receive':           'inventory',

    # Billing
    'bill_list':            'billing_view',
    'bill_add':             'billing',
    'bill_detail':          'billing_view',
    'bill_edit':            'billing',
    'add_payment':          'billing',
    'waive_bill':           'billing',
    'print_receipt':        'billing_view',

    # PDF exports
    'pdf_patient':          'clinical',
    'pdf_prenatal':         'clinical',
    'pdf_delivery':         'clinical',
    'pdf_soa':              'billing_view',
    'pdf_newborn':          'clinical',

    # Staff management
    'staff_list':           'staff_mgmt',
    'staff_add':            'staff_mgmt',
    'staff_edit':           'staff_mgmt',
    'staff_deactivate':     'staff_mgmt',
    'staff_reactivate':     'staff_mgmt',

    # Audit logs
    'auditlog_list':        'admin',
}


def get_user_role(user):
    """Return the role string for a user, or None if no profile."""
    try:
        return user.staff_profile.role
    except Exception:
        return None


def user_has_permission(user, group):
    """Check if user's role is in the permission group."""
    if not user.is_authenticated:
        return False
    # Django superusers always have full access
    if user.is_superuser:
        return True
    role = get_user_role(user)
    if not role:
        return False
    allowed = PERMISSION_GROUPS.get(group, [])
    return role in allowed


def check_url_permission(user, url_name):
    """Check if user can access a given named URL."""
    group = URL_PERMISSIONS.get(url_name)
    if group is None:
        return True   # Not mapped = allow (login still required)
    return user_has_permission(user, group)


def role_required(group):
    """
    Decorator that checks if the logged-in user's role is in the permission group.

    @login_required
    @role_required('billing')
    def bill_add(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not user_has_permission(request.user, group):
                role = get_user_role(request.user) or 'unknown'
                messages.error(
                    request,
                    f"Access denied. Your role ({role.replace('_', ' ').title()}) "
                    f"does not have permission for this action."
                )
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
