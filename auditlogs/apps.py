from django.apps import AppConfig


class AuditlogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auditlogs'

    def ready(self):
        from .middleware import setup_audit_signals
        setup_audit_signals()
