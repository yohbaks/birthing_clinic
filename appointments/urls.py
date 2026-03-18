from django.urls import path
from . import views
urlpatterns = [
    path("",                         views.appointment_list,         name="appointment_list"),
    path("add/",                     views.appointment_add,          name="appointment_add"),
    path("<int:pk>/edit/",           views.appointment_edit,         name="appointment_edit"),
    path("<int:pk>/update-status/",  views.update_status,            name="appointment_status"),
    path("<int:pk>/print-slip/",     views.appointment_print_slip,   name="appointment_print_slip"),
    path("queue/",                   views.queue_display,            name="queue_display"),
    path("queue/manage/",            views.queue_manage,             name="queue_manage"),
    path("queue/add/",               views.queue_add,                name="queue_add"),
    path("queue/<int:pk>/update/",   views.queue_update,             name="queue_update"),
    path("queue/api/",               views.queue_api,                name="queue_api"),
]
