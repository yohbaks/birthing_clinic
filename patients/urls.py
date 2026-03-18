from django.urls import path
from . import views
urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('add/', views.patient_add, name='patient_add'),
    path('<int:pk>/', views.patient_profile, name='patient_profile'),
    path('<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    path('<int:pk>/add-history/', views.add_pregnancy_history, name='add_pregnancy_history'),
    path('<int:pk>/deactivate/', views.deactivate_patient, name='deactivate_patient'),
    path('<int:pk>/reactivate/', views.reactivate_patient, name='reactivate_patient'),
    path('inactive/', views.inactive_patients, name='inactive_patients'),
    path('check-duplicate/', views.check_duplicate_patient, name='check_duplicate_patient'),
    path('<int:pk>/add-immunization/', views.add_maternal_immunization, name='add_maternal_immunization'),
    path('immunization/<int:pk>/delete/', views.delete_maternal_immunization, name='delete_maternal_immunization'),
    path('import/', views.import_patients_csv, name='import_patients_csv'),
]
