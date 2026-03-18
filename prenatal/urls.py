from django.urls import path
from . import views
urlpatterns = [
    path('', views.prenatal_list, name='prenatal_list'),
    path('add/', views.prenatal_add, name='prenatal_add'),
    path('<int:pk>/', views.prenatal_detail, name='prenatal_detail'),
    path('<int:pk>/edit/', views.prenatal_edit, name='prenatal_edit'),
    path('<int:pk>/add-lab/', views.add_lab_request, name='add_lab_request'),
    path('patient/<int:patient_pk>/', views.patient_prenatal, name='patient_prenatal'),
    path('patient/<int:patient_pk>/add-ultrasound/', views.add_ultrasound, name='add_ultrasound'),
]
