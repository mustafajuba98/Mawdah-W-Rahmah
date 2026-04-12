from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.matching.models import IntroductionRequest
from apps.matching.services import apply_moderator_decision
from services.audit import log_action

PER_PAGE = 15


def _is_moderation_staff(u):
    return u.is_authenticated and (
        u.is_superuser
        or u.groups.filter(name__in=("platform_admin", "moderator")).exists()
    )


def _is_platform_admin(u):
    return u.is_authenticated and (
        u.is_superuser or u.groups.filter(name="platform_admin").exists()
    )


def _paginate(request, queryset):
    paginator = Paginator(queryset, PER_PAGE)
    p = request.GET.get("page") or 1
    try:
        return paginator.page(p)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def _moderation_ctx(request, tab: str):
    return {
        "moderation_tab": tab,
        "show_accounts_tab": _is_platform_admin(request.user),
    }


@user_passes_test(_is_moderation_staff)
def moderation_home(request):
    return redirect("moderation_pending_profiles")


@user_passes_test(_is_moderation_staff)
def moderation_pending_profiles(request):
    qs = (
        User.objects.filter(profile_status=User.ProfileStatus.PENDING_REVIEW)
        .select_related("applicant_profile")
        .order_by("-date_joined")
    )
    ctx = _moderation_ctx(request, "profiles")
    ctx["page_obj"] = _paginate(request, qs)
    return render(request, "moderation/pending_profiles.html", ctx)


@user_passes_test(_is_moderation_staff)
def moderation_intros_waiting_recipient(request):
    qs = (
        IntroductionRequest.objects.filter(status=IntroductionRequest.Status.PENDING)
        .select_related(
            "requester",
            "recipient",
            "requester__applicant_profile",
            "recipient__applicant_profile",
        )
        .order_by("-created_at")
    )
    ctx = _moderation_ctx(request, "intros_recipient")
    ctx["page_obj"] = _paginate(request, qs)
    return render(request, "moderation/intros_waiting_recipient.html", ctx)


@user_passes_test(_is_moderation_staff)
def moderation_intros_waiting_decision(request):
    qs = (
        IntroductionRequest.objects.filter(
            status=IntroductionRequest.Status.PENDING_MODERATOR,
        )
        .select_related(
            "requester",
            "recipient",
            "requester__applicant_profile",
            "recipient__applicant_profile",
        )
        .order_by("-created_at")
    )
    ctx = _moderation_ctx(request, "intros_mod")
    ctx["page_obj"] = _paginate(request, qs)
    return render(request, "moderation/intros_waiting_decision.html", ctx)


@user_passes_test(_is_platform_admin)
def moderation_active_accounts(request):
    qs = User.objects.filter(profile_status=User.ProfileStatus.ACTIVE).order_by("email")
    ctx = _moderation_ctx(request, "accounts")
    ctx["page_obj"] = _paginate(request, qs)
    return render(request, "moderation/active_accounts.html", ctx)


@user_passes_test(_is_moderation_staff)
def approve_profile(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        u.profile_status = User.ProfileStatus.ACTIVE
        u.is_active = True
        u.save(update_fields=["profile_status", "is_active"])
        log_action(request.user, "profile_approved", target_user=u, metadata={})
        messages.success(request, "تم تفعيل الملف.")
        return redirect("moderation_pending_profiles")
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
        return redirect("moderation_pending_profiles")
    return render(request, "moderation/confirm_profile.html", {"target_user": u, "action": "reject"})


@user_passes_test(_is_platform_admin)
def suspend_user(request, pk):
    u = get_object_or_404(User, pk=pk)
    if u.is_superuser:
        messages.error(request, "لا يمكن إيقاف مدير النظام.")
        return redirect("moderation_active_accounts")
    if request.method == "POST":
        u.profile_status = User.ProfileStatus.SUSPENDED
        u.is_active = False
        u.save(update_fields=["profile_status", "is_active"])
        log_action(request.user, "user_suspended", target_user=u, metadata={})
        messages.warning(request, "تم إيقاف الحساب.")
        return redirect("moderation_active_accounts")
    return render(request, "moderation/suspend.html", {"target_user": u})


@user_passes_test(_is_moderation_staff)
def decide_intro(request, pk):
    intro = get_object_or_404(IntroductionRequest, pk=pk)
    if intro.status != IntroductionRequest.Status.PENDING_MODERATOR:
        messages.error(request, "الطلب ليس بانتظار المشرف.")
        return redirect("moderation_intros_waiting_decision")
    if request.method == "POST":
        approve = request.POST.get("decision") == "approve"
        notes = request.POST.get("notes", "")[:4000]
        apply_moderator_decision(intro, request.user, approve, notes)
        messages.success(request, "تم تسجيل قرار المشرف.")
        return redirect("moderation_intros_waiting_decision")
    return render(request, "moderation/decide_intro.html", {"intro": intro})
