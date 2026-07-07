from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SignupView,
    VerifySignupOTPView,
    LoginView,
    MeView,
    ForgotPasswordView,
    VerifyForgotPasswordOTPView,
    ResetPasswordView,
)

urlpatterns = [
    # ── signup (2-step OTP flow) ─────────────────────────────────
    path("signup",               SignupView.as_view(),              name="teacher-signup"),
    path("signup/verify",        VerifySignupOTPView.as_view(),     name="teacher-signup-verify"),

    # ── login ─────────────────────────────────────────────────────
    path("login",                LoginView.as_view(),               name="teacher-login"),

    # ── token refresh ────────────────────────────────────────────
    path("token/refresh",        TokenRefreshView.as_view(),        name="token-refresh"),

    # ── me ───────────────────────────────────────────────────────
    path("me",                   MeView.as_view(),                  name="teacher-me"),

    # ── forgot / reset password (3-step OTP flow) ────────────────
    path("forgot-password",        ForgotPasswordView.as_view(),           name="teacher-forgot-password"),
    path("forgot-password/verify", VerifyForgotPasswordOTPView.as_view(),  name="teacher-forgot-password-verify"),
    path("reset-password",         ResetPasswordView.as_view(),            name="teacher-reset-password"),
]
