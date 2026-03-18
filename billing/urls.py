from django.urls import path
from . import views
urlpatterns = [
    path('', views.bill_list, name='bill_list'),
    path('add/', views.bill_add, name='bill_add'),
    path('<int:pk>/', views.bill_detail, name='bill_detail'),
    path('<int:pk>/payment/', views.add_payment, name='add_payment'),
    path('<int:pk>/receipt/', views.print_receipt, name='print_receipt'),
    path('<int:pk>/edit/', views.bill_edit, name='bill_edit'),
    path('<int:pk>/waive/', views.waive_bill, name='waive_bill'),
    path('from-delivery/<int:delivery_pk>/', views.bill_from_delivery, name='bill_from_delivery'),
    path('philhealth/', views.philhealth_list, name='philhealth_list'),
    path('philhealth/add/', views.philhealth_add, name='philhealth_add'),
    path('philhealth/<int:pk>/update/', views.philhealth_update, name='philhealth_update'),
    path('eod/', views.eod_report, name='eod_report'),
]
