from django.urls import path
from . import views
urlpatterns = [
    path('', views.delivery_list, name='delivery_list'),
    path('admit/', views.delivery_admit, name='delivery_admit'),
    path('<int:pk>/', views.delivery_detail, name='delivery_detail'),
    path('<int:pk>/monitor/', views.labor_monitor, name='labor_monitor'),
    path('<int:pk>/add-monitoring/', views.add_monitoring, name='add_monitoring'),
    path('<int:pk>/add-complication/', views.add_complication, name='add_complication'),
]
