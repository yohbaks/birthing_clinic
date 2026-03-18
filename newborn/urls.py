from django.urls import path
from . import views
urlpatterns = [
    path('', views.newborn_list, name='newborn_list'),
    path('add/', views.newborn_add, name='newborn_add'),
    path('<int:pk>/', views.newborn_detail, name='newborn_detail'),
    path('<int:pk>/add-immunization/', views.add_immunization, name='add_immunization'),
    path('<int:pk>/discharge/', views.discharge_newborn, name='discharge_newborn'),
    path('<int:pk>/edit/', views.newborn_edit, name='newborn_edit'),
]
