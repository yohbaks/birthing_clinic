from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.permissions import role_required
from .models import AuditLog
import json

@login_required
@role_required('admin')
def auditlog_list(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')

    # Filters
    action_filter  = request.GET.get('action', '')
    module_filter  = request.GET.get('module', '')
    user_filter    = request.GET.get('user', '')
    date_from      = request.GET.get('date_from', '')
    date_to        = request.GET.get('date_to', '')

    if action_filter:
        logs = logs.filter(action=action_filter)
    if module_filter:
        logs = logs.filter(module=module_filter)
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    # Distinct values for filter dropdowns
    all_actions = AuditLog.objects.values_list('action', flat=True).distinct().order_by('action')
    all_modules = AuditLog.objects.values_list('module', flat=True).distinct().order_by('module')

    logs = logs[:500]  # Cap at 500 rows

    return render(request, 'auditlogs/auditlog_list.html', {
        'logs': logs,
        'action_filter': action_filter,
        'module_filter': module_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'all_actions': all_actions,
        'all_modules': all_modules,
    })


@login_required
@role_required('admin')
def auditlog_detail(request, pk):
    log = get_object_or_404(AuditLog, pk=pk)
    old_values = {}
    new_values = {}
    diff = []

    try:
        old_values = json.loads(log.old_values) if log.old_values else {}
    except Exception:
        old_values = {'raw': log.old_values}

    try:
        new_values = json.loads(log.new_values) if log.new_values else {}
    except Exception:
        new_values = {'raw': log.new_values}

    # Build diff: fields that changed
    if log.action == 'update' and old_values and new_values:
        all_keys = set(old_values.keys()) | set(new_values.keys())
        for key in sorted(all_keys):
            old_val = old_values.get(key, '—')
            new_val = new_values.get(key, '—')
            if str(old_val) != str(new_val):
                diff.append({
                    'field': key.replace('_', ' ').title(),
                    'old': old_val,
                    'new': new_val,
                })

    return render(request, 'auditlogs/auditlog_detail.html', {
        'log': log,
        'old_values': old_values,
        'new_values': new_values,
        'diff': diff,
    })
