from django.urls import path

from . import views

urlpatterns = [
    path("", views.conversation_list, name="conversation_list"),
    path("<int:pk>/", views.conversation_room, name="conversation_room"),
    path("<int:pk>/send/", views.post_message, name="conversation_post"),
    path("<int:pk>/poll/", views.long_poll_messages, name="conversation_poll"),
]
