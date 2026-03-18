from django.contrib import admin
from .models import NewbornRecord, NewbornImmunization

class ImmunizationInline(admin.TabularInline):
    model = NewbornImmunization
    extra = 0

@admin.register(NewbornRecord)
class NewbornAdmin(admin.ModelAdmin):
    list_display = ['baby_id', 'baby_name', 'mother', 'birth_datetime', 'gender', 'weight_grams', 'birth_status']
    list_filter = ['gender', 'birth_status']
    search_fields = ['baby_id', 'baby_name', 'mother__full_name']
    inlines = [ImmunizationInline]
