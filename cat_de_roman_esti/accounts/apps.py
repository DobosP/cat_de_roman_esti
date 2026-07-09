from __future__ import annotations

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cat_de_roman_esti.accounts"
    label = "cat_accounts"
    verbose_name = "cât-de-român-ești accounts"
