from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'module', 'record_id', 'ip_address']
    list_filter = ['action', 'module']
    search_fields = ['user__username', 'description']
    readonly_fields = ['timestamp', 'user', 'action', 'module', 'record_id', 'description', 'old_values', 'new_values', 'ip_address']
