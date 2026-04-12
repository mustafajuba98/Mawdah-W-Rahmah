from django.urls import path

from . import views

urlpatterns = [
    path("edit/", views.profile_edit, name="profile_edit"),
    path("<int:pk>/", views.ProfileDetailView.as_view(), name="profile_detail"),
]
