from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_user", "created_at")
    list_filter = ("action",)
    search_fields = ("actor__email", "target_user__email")
