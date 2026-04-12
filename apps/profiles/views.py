from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView

from apps.accounts.models import User
from apps.accounts.roles import is_moderation_portal_user
from apps.moderation.models import AuditLog
from services.access import (
    can_view_contact_details,
    can_view_full_profile,
    can_view_profile_browse,
    log_profile_view,
)
from services.audit import log_action

from .forms import ApplicantProfileForm, BrideExtraForm, GroomExtraForm, ProfileMediaForm
from .models import ApplicantProfile, BrideExtendedProfile, GroomExtendedProfile


@login_required
def profile_edit(request):
    user = request.user
    gender = user.applicant_gender
    if not gender:
        if is_moderation_portal_user(user):
            return render(request, "profiles/staff_no_applicant.html")
        messages.error(request, "حدّد نوع مقدّم الطلب عند التسجيل أولاً.")
        return redirect("home")

    profile = ApplicantProfile.objects.filter(user=user).first()

    if request.method == "POST":
        form = ApplicantProfileForm(request.POST, instance=profile)
        extra_form = None
        if profile:
            if gender == User.ApplicantGender.MALE:
                g, _ = GroomExtendedProfile.objects.get_or_create(profile=profile)
                extra_form = GroomExtraForm(request.POST, instance=g)
            else:
                b, _ = BrideExtendedProfile.objects.get_or_create(profile=profile)
                extra_form = BrideExtraForm(request.POST, instance=b)
        media_form = ProfileMediaForm(request.POST, request.FILES)

        if form.is_valid() and (extra_form is None or extra_form.is_valid()):
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.user = user
                obj.applicant_gender = gender
                obj.save()
                profile = obj
                if extra_form:
                    ex = extra_form.save(commit=False)
                    ex.profile = profile
                    ex.save()
                user.profile_status = User.ProfileStatus.PENDING_REVIEW
                user.save(update_fields=["profile_status"])
                if media_form.is_valid() and media_form.cleaned_data.get("image"):
                    m = media_form.save(commit=False)
                    m.profile = profile
                    m.save()
            messages.success(request, "تم حفظ الاستمارة وهي الآن قيد مراجعة المشرف.")
            return redirect("home")
        err_parts = []
        for fname, elist in form.errors.items():
            label = fname
            for msg in elist:
                err_parts.append(f"{label}: {msg}")
        if extra_form is not None:
            for fname, elist in extra_form.errors.items():
                for msg in elist:
                    err_parts.append(f"{fname}: {msg}")
        if err_parts:
            messages.error(
                request,
                "تعذّر الحفظ — " + " — ".join(err_parts[:12]),
            )
    else:
        form = ApplicantProfileForm(instance=profile)
        extra_form = None
        if profile:
            if gender == User.ApplicantGender.MALE:
                g, _ = GroomExtendedProfile.objects.get_or_create(profile=profile)
                extra_form = GroomExtraForm(instance=g)
            else:
                b, _ = BrideExtendedProfile.objects.get_or_create(profile=profile)
                extra_form = BrideExtraForm(instance=b)
        media_form = ProfileMediaForm()

    return render(
        request,
        "profiles/edit.html",
        {
            "form": form,
            "extra_form": extra_form,
            "media_form": media_form,
            "profile": profile,
        },
    )


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "profiles/detail.html"
    context_object_name = "target_user"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return User.objects.select_related("applicant_profile").prefetch_related(
            "applicant_profile__media_items",
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        target = self.object
        viewer = self.request.user
        ctx["browse_ok"] = can_view_profile_browse(viewer, target)
        ctx["full_ok"] = can_view_full_profile(viewer, target)
        ctx["contact_ok"] = can_view_contact_details(viewer, target)
        if ctx["browse_ok"]:
            log_profile_view(AuditLog, viewer, target, "browse", self.request)
        elif ctx["full_ok"]:
            log_profile_view(AuditLog, viewer, target, "full", self.request)
        if ctx.get("contact_ok") and viewer.pk != target.pk:
            log_action(viewer, "contact_details_viewed", target_user=target, metadata={})
        return ctx
