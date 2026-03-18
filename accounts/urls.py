from django.urls import path
from . import views
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_add, name='staff_add'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('profile/', views.my_profile, name='my_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('staff/<int:pk>/deactivate/', views.staff_deactivate, name='staff_deactivate'),
    path('staff/<int:pk>/reactivate/', views.staff_reactivate, name='staff_reactivate'),
    path('clinic-settings/', views.clinic_settings, name='clinic_settings'),
    path('sessions/', views.session_monitor, name='session_monitor'),
]
