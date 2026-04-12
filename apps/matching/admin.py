from django.contrib import admin

from .models import IntroductionRequest


@admin.register(IntroductionRequest)
class IntroductionRequestAdmin(admin.ModelAdmin):
    list_display = ("requester", "recipient", "status", "created_at", "decided_at")
    list_filter = ("status",)
    search_fields = ("requester__email", "recipient__email")
