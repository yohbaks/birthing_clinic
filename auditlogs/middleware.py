"""
Audit logging middleware and helpers.

Auto-logs all clinical data changes via Django signals.
Manual logging via log_action() for custom events.
"""
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog
import json


class AuditLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.audit_ip = self._get_client_ip(request)

    def _get_client_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


def log_action(user, action, module, record_id='', description='',
               old_values='', new_values='', ip=None, request=None):
    """Create an audit log entry."""
    if request and not ip:
        ip = getattr(request, 'audit_ip', None) or _get_ip(request)
    try:
        AuditLog.objects.create(
            user=user if hasattr(user, 'pk') else None,
            action=action,
            module=module,
            record_id=str(record_id),
            description=description,
            old_values=old_values if isinstance(old_values, str) else json.dumps(old_values, default=str),
            new_values=new_values if isinstance(new_values, str) else json.dumps(new_values, default=str),
            ip_address=ip or '',
        )
    except Exception:
        pass  # Never let audit logging crash the app


def _get_ip(request):
    if request is None:
        return ''
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _model_to_dict(instance):
    """Serialize model instance to dict for audit trail."""
    data = {}
    for field in instance._meta.fields:
        try:
            val = getattr(instance, field.name)
            if hasattr(val, 'pk'):
                data[field.name] = str(val)
            else:
                data[field.name] = str(val) if val is not None else None
        except Exception:
            pass
    return data


# ── Django Signals for auto-audit logging ─────────────────────────────────────

def setup_audit_signals():
    """
    Wire up post_save and post_delete signals for all clinical models.
    Called once from AppConfig.ready().
    """
    from django.db.models.signals import post_save, post_delete
    from django.dispatch import receiver

    # Models to track and their module labels
    TRACKED_MODELS = {
        'patients.Patient':            'Patients',
        'prenatal.PrenatalVisit':      'Prenatal',
        'prenatal.LabRequest':         'Prenatal',
        'prenatal.UltrasoundRecord':   'Prenatal',
        'appointments.Appointment':    'Appointments',
        'delivery.DeliveryRecord':     'Delivery',
        'delivery.LaborMonitoring':    'Delivery',
        'delivery.DeliveryComplication':'Delivery',
        'newborn.NewbornRecord':       'Newborn',
        'newborn.NewbornImmunization': 'Newborn',
        'inventory.InventoryItem':     'Inventory',
        'inventory.StockTransaction':  'Inventory',
        'billing.Bill':                'Billing',
        'billing.Payment':             'Billing',
        'accounts.StaffProfile':       'Staff',
    }

    # Store pre-save snapshots
    _pre_save_data = {}

    from django.db.models.signals import pre_save

    def make_pre_save_handler(module_label):
        def pre_save_handler(sender, instance, **kwargs):
            if instance.pk:
                try:
                    old = sender.objects.get(pk=instance.pk)
                    _pre_save_data[f'{sender.__name__}_{instance.pk}'] = _model_to_dict(old)
                except sender.DoesNotExist:
                    pass
        return pre_save_handler

    def make_post_save_handler(module_label):
        def post_save_handler(sender, instance, created, **kwargs):
            # Get current user from threading local (set by middleware)
            user = _get_current_user()
            action = 'create' if created else 'update'
            new_data = _model_to_dict(instance)
            old_data = {}
            if not created:
                key = f'{sender.__name__}_{instance.pk}'
                old_data = _pre_save_data.pop(key, {})

            # Only log updates if something actually changed
            if not created and old_data == new_data:
                return

            description = f"{action.title()} {sender.__name__} #{instance.pk}"
            try:
                description = f"{action.title()} {sender.__name__}: {str(instance)}"
            except Exception:
                pass

            log_action(
                user=user,
                action=action,
                module=module_label,
                record_id=instance.pk,
                description=description[:500],
                old_values=old_data,
                new_values=new_data,
            )
        return post_save_handler

    def make_post_delete_handler(module_label):
        def post_delete_handler(sender, instance, **kwargs):
            user = _get_current_user()
            description = f"Delete {sender.__name__} #{instance.pk}"
            try:
                description = f"Delete {sender.__name__}: {str(instance)}"
            except Exception:
                pass
            log_action(
                user=user,
                action='delete',
                module=module_label,
                record_id=instance.pk,
                description=description[:500],
                old_values=_model_to_dict(instance),
            )
        return post_delete_handler

    # Connect signals for each tracked model
    from django.apps import apps
    for model_path, module_label in TRACKED_MODELS.items():
        try:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)
            pre_save.connect(make_pre_save_handler(module_label), sender=model, weak=False)
            post_save.connect(make_post_save_handler(module_label), sender=model, weak=False)
            post_delete.connect(make_post_delete_handler(module_label), sender=model, weak=False)
        except Exception:
            pass


# ── Thread-local current user ──────────────────────────────────────────────────
# Store the current request user so signals can reference it

import threading
_thread_local = threading.local()


def _get_current_user():
    return getattr(_thread_local, 'user', None)


class CurrentUserMiddleware(MiddlewareMixin):
    """Stores the current user in thread-local for signal access."""
    def process_request(self, request):
        _thread_local.user = getattr(request, 'user', None)

    def process_response(self, request, response):
        _thread_local.user = None
        return response
