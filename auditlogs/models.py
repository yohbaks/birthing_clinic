from django.db import models
from django.contrib.auth.models import User

class AuditLog(models.Model):
    ACTION_TYPES = [
        ('create','Create'),('update','Update'),('delete','Delete'),
        ('login','Login'),('logout','Logout'),('view','View'),
        ('export','Export'),('print','Print'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    module = models.CharField(max_length=100)
    record_id = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    old_values = models.TextField(blank=True)
    new_values = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user = self.user.username if self.user else 'System'
        return f"{user} {self.action} {self.module} at {self.timestamp}"
