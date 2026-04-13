from django.urls import path

from . import views

urlpatterns = [
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("verify-email/", views.VerifyEmailView.as_view(), name="verify_email"),
    path(
        "verify-email/resend/",
        views.ResendVerificationView.as_view(),
        name="resend_verification",
    ),
    path("login/", views.EmailLoginView.as_view(), name="login"),
    path("logout/", views.AppLogoutView.as_view(), name="logout"),
]
