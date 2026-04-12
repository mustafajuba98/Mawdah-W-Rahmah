from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import User
from apps.matching.models import IntroductionRequest
from apps.matching.services import apply_moderator_decision
from services.audit import log_action


def _is_moderation_staff(u):
    return u.is_authenticated and (
        u.is_superuser
        or u.groups.filter(name__in=("platform_admin", "moderator")).exists()
    )


def _is_platform_admin(u):
    return u.is_authenticated and (
        u.is_superuser or u.groups.filter(name="platform_admin").exists()
    )


@user_passes_test(_is_moderation_staff)
def moderation_home(request):
    pending_users = User.objects.filter(
        profile_status=User.ProfileStatus.PENDING_REVIEW,
    ).select_related("applicant_profile")
    pending_intros = IntroductionRequest.objects.filter(
        status=IntroductionRequest.Status.PENDING_MODERATOR,
    ).select_related("requester", "recipient")
    active_for_suspend = []
    if _is_platform_admin(request.user):
        active_for_suspend = User.objects.filter(
            profile_status=User.ProfileStatus.ACTIVE,
        ).order_by("email")[:100]
    return render(
        request,
        "moderation/home.html",
        {
            "pending_users": pending_users,
            "pending_intros": pending_intros,
            "active_for_suspend": active_for_suspend,
            "is_platform_admin": _is_platform_admin(request.user),
        },
    )


@user_passes_test(_is_moderation_staff)
def approve_profile(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        u.profile_status = User.ProfileStatus.ACTIVE
        u.is_active = True
        u.save(update_fields=["profile_status", "is_active"])
        log_action(request.user, "profile_approved", target_user=u, metadata={})
        messages.success(request, "تم تفعيل الملف.")
        return redirect("moderation_home")
    return render(request, "moderation/confirm_profile.html", {"target_user": u, "action": "approve"})


@user_passes_test(_is_moderation_staff)
def reject_profile(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        u.profile_status = User.ProfileStatus.REJECTED
        u.is_active = False
        u.save(update_fields=["profile_status", "is_active"])
        log_action(request.user, "profile_rejected", target_user=u, metadata={})
        messages.warning(request, "تم رفض الملف وإيقاف الدخول.")
        return redirect("moderation_home")
    return render(request, "moderation/confirm_profile.html", {"target_user": u, "action": "reject"})


@user_passes_test(_is_platform_admin)
def suspend_user(request, pk):
    u = get_object_or_404(User, pk=pk)
    if u.is_superuser:
        messages.error(request, "لا يمكن إيقاف مدير النظام.")
        return redirect("moderation_home")
    if request.method == "POST":
        u.profile_status = User.ProfileStatus.SUSPENDED
        u.is_active = False
        u.save(update_fields=["profile_status", "is_active"])
        log_action(request.user, "user_suspended", target_user=u, metadata={})
        messages.warning(request, "تم إيقاف الحساب.")
        return redirect("moderation_home")
    return render(request, "moderation/suspend.html", {"target_user": u})


@user_passes_test(_is_moderation_staff)
def decide_intro(request, pk):
    intro = get_object_or_404(IntroductionRequest, pk=pk)
    if intro.status != IntroductionRequest.Status.PENDING_MODERATOR:
        messages.error(request, "الطلب ليس بانتظار المشرف.")
        return redirect("moderation_home")
    if request.method == "POST":
        approve = request.POST.get("decision") == "approve"
        notes = request.POST.get("notes", "")[:4000]
        apply_moderator_decision(intro, request.user, approve, notes)
        messages.success(request, "تم تسجيل قرار المشرف.")
        return redirect("moderation_home")
    return render(request, "moderation/decide_intro.html", {"intro": intro})
