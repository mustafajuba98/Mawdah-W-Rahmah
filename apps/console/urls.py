from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="console_dashboard"),
    path("users/", views.ConsoleUserListView.as_view(), name="console_user_list"),
    path("users/new/", views.user_create, name="console_user_create"),
    path("users/<int:pk>/", views.user_edit, name="console_user_edit"),
]
