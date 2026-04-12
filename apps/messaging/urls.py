from django.urls import path

from . import views

urlpatterns = [
    path("", views.conversation_list, name="conversation_list"),
    path("<int:pk>/", views.conversation_room, name="conversation_room"),
    path("<int:pk>/send/", views.post_message, name="conversation_post"),
    path("<int:pk>/poll/", views.long_poll_messages, name="conversation_poll"),
    path("<int:pk>/close/", views.conversation_close, name="conversation_close"),
    path("<int:pk>/reopen/request/", views.conversation_request_reopen, name="conversation_reopen_request"),
    path("<int:pk>/reopen/respond/", views.conversation_respond_reopen, name="conversation_reopen_respond"),
]
