from django.contrib import admin

from .models import ApplicantProfile, BrideExtendedProfile, GroomExtendedProfile


@admin.register(ApplicantProfile)
class ApplicantProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "governorate", "applicant_gender", "marital_status")
    list_filter = ("governorate", "applicant_gender", "marital_status")
    search_fields = ("full_name", "user__email")


@admin.register(GroomExtendedProfile)
class GroomExtendedProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(BrideExtendedProfile)
class BrideExtendedProfileAdmin(admin.ModelAdmin):
    pass
