from django.urls import path
from . import views
urlpatterns = [
    path("",                  views.postpartum_list,    name="postpartum_list"),
    path("add/",              views.postpartum_add,     name="postpartum_add"),
    path("<int:pk>/",         views.postpartum_detail,  name="postpartum_detail"),
    path("<int:pk>/edit/",    views.postpartum_edit,    name="postpartum_edit"),
    path("patient/<int:pk>/", views.patient_postpartum, name="patient_postpartum"),
]
