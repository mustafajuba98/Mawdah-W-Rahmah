from django.urls import path

from . import views

urlpatterns = [
    path("", views.BrowseListView.as_view(), name="browse"),
    path("intro/<int:pk>/", views.send_introduction, name="send_intro"),
    path("inbox/", views.intro_inbox, name="intro_inbox"),
    path("inbox/accept/<int:pk>/", views.accept_introduction, name="accept_intro"),
]
