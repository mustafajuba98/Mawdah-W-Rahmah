from django.urls import path

from . import views

urlpatterns = [
    path("", views.moderation_home, name="moderation_home"),
    path("profiles/pending/", views.moderation_pending_profiles, name="moderation_pending_profiles"),
    path(
        "intros/waiting-recipient/",
        views.moderation_intros_waiting_recipient,
        name="moderation_intros_waiting_recipient",
    ),
    path(
        "intros/waiting-decision/",
        views.moderation_intros_waiting_decision,
        name="moderation_intros_waiting_decision",
    ),
    path("accounts/active/", views.moderation_active_accounts, name="moderation_active_accounts"),
    path("profiles/<int:pk>/approve/", views.approve_profile, name="moderation_approve_profile"),
    path("profiles/<int:pk>/reject/", views.reject_profile, name="moderation_reject_profile"),
    path("users/<int:pk>/suspend/", views.suspend_user, name="moderation_suspend_user"),
    path("intros/<int:pk>/decide/", views.decide_intro, name="moderation_decide_intro"),
]
