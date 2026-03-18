from django.urls import path
from . import views, pdf_views
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('daily-census/', views.daily_census, name='daily_census'),
    path('delivery-report/', views.delivery_report, name='delivery_report'),
    path('collection-report/', views.collection_report, name='collection_report'),
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    # PDF exports
    path('pdf/patient/<int:pk>/', pdf_views.pdf_patient_summary, name='pdf_patient'),
    path('pdf/prenatal/<int:pk>/', pdf_views.pdf_prenatal_visit, name='pdf_prenatal'),
    path('pdf/delivery/<int:pk>/', pdf_views.pdf_delivery_certificate, name='pdf_delivery'),
    path('pdf/bill/<int:pk>/', pdf_views.pdf_soa, name='pdf_soa'),
    path('pdf/newborn/<int:pk>/', pdf_views.pdf_newborn_record, name='pdf_newborn'),
    path('monthly/', views.monthly_report, name='monthly_report'),
    path('newborn-summary/', views.newborn_report, name='newborn_report'),
    path('export/', views.export_center, name='export_center'),
    path('export/<str:model_type>/', views.export_csv, name='export_csv'),
    path('system-health/', views.system_health, name='system_health'),
    path('fhsis/', views.fhsis_report, name='fhsis_report'),
    path('morbidity/', views.morbidity_report, name='morbidity_report'),
]
