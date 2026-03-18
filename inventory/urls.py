from django.urls import path
from . import views
urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('add/', views.item_add, name='item_add'),
    path('<int:pk>/', views.item_detail, name='item_detail'),
    path('<int:pk>/edit/', views.item_edit, name='item_edit'),
    path('stock-in/', views.stock_in, name='stock_in'),
    path('stock-out/', views.stock_out, name='stock_out'),
    path('low-stock/', views.low_stock, name='low_stock'),
    path('expiry-report/', views.expiry_report, name='expiry_report'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('purchase-orders/', views.purchase_order_list, name='po_list'),
    path('purchase-orders/add/', views.purchase_order_add, name='po_add'),
    path('purchase-orders/<int:pk>/', views.purchase_order_detail, name='po_detail'),
    path('purchase-orders/<int:pk>/receive/', views.receive_purchase_order, name='po_receive'),
    path('<int:pk>/toggle-active/', views.item_toggle_active, name='item_toggle_active'),
]
