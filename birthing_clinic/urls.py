from django.contrib import admin
from django.urls import path, include
from birthing_clinic import search_view as sv
from reports import drug_checker as dc
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('search/', sv.global_search, name='global_search'),
    path('drug-check/', dc.check_drug_interactions, name='drug_check'),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('reports.urls')),
    path('patients/', include('patients.urls')),
    path('prenatal/', include('prenatal.urls')),
    path('appointments/', include('appointments.urls')),
    path('delivery/', include('delivery.urls')),
    path('newborn/', include('newborn.urls')),
    path('inventory/', include('inventory.urls')),
    path('billing/', include('billing.urls')),
    path('auditlogs/', include('auditlogs.urls')),
    path('postpartum/', include('postpartum.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
