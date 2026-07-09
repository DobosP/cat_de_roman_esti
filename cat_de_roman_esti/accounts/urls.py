"""Account API routes (mounted before the /api 404 guard by web/urls.py)."""

from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("api/me", views.MeView.as_view()),
    path("api/me/consent", views.ConsentView.as_view()),
    path("api/me/scores", views.ScoresView.as_view()),
    path("api/me/delete", views.DeleteAccountView.as_view()),
    path("api/auth/logout", views.LogoutView.as_view()),
]
