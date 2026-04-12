from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from apps.accounts.models import User
from apps.profiles.constants import EGYPT_GOVERNORATES
from services.access import can_view_profile_browse
from services.audit import log_action

from .models import IntroductionRequest


class BrowseListView(LoginRequiredMixin, ListView):
    template_name = "matching/browse.html"
    context_object_name = "users"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.profile_status != User.ProfileStatus.ACTIVE:
            messages.warning(request, "التصفح متاح بعد تفعيل حسابك من المشرف.")
            return redirect("home")
        if not hasattr(request.user, "applicant_profile"):
            messages.warning(request, "أكمل الاستمارة أولاً.")
            return redirect("profile_edit")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        viewer = self.request.user
        if viewer.applicant_gender == User.ApplicantGender.MALE:
            opposite = User.ApplicantGender.FEMALE
        else:
            opposite = User.ApplicantGender.MALE

        qs = (
            User.objects.filter(
                profile_status=User.ProfileStatus.ACTIVE,
                applicant_profile__applicant_gender=opposite,
            )
            .select_related("applicant_profile")
            .exclude(pk=viewer.pk)
        )

        gov = self.request.GET.get("governorate")
        if gov:
            qs = qs.filter(applicant_profile__governorate=gov)
        edu = self.request.GET.get("education")
        if edu:
            qs = qs.filter(applicant_profile__education=edu)
        ms = self.request.GET.get("marital_status")
        if ms:
            qs = qs.filter(applicant_profile__marital_status=ms)

        today = date.today()
        amax = self.request.GET.get("age_max")
        amin = self.request.GET.get("age_min")
        if amax:
            y_min = today.year - int(amax) - 1
            qs = qs.filter(applicant_profile__birth_date__year__gte=y_min)
        if amin:
            y_max = today.year - int(amin) + 1
            qs = qs.filter(applicant_profile__birth_date__year__lte=y_max)

        return qs.order_by("-applicant_profile__submitted_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["governorate_choices"] = EGYPT_GOVERNORATES
        ctx["filters"] = self.request.GET
        return ctx


@login_required
def send_introduction(request, pk):
    recipient = get_object_or_404(User, pk=pk)
    if not can_view_profile_browse(request.user, recipient):
        messages.error(request, "لا يمكن إرسال طلب لهذا الملف.")
        return redirect("browse")
    if request.method == "POST":
        msg = request.POST.get("message", "")[:2000]
        intro, created = IntroductionRequest.objects.get_or_create(
            requester=request.user,
            recipient=recipient,
            defaults={"message": msg, "status": IntroductionRequest.Status.PENDING},
        )
        if not created:
            messages.info(request, "سبق إرسال طلب لهذا الشخص.")
        else:
            log_action(request.user, "intro_sent", target_user=recipient, metadata={})
            messages.success(request, "تم إرسال طلب الرؤية الشرعية.")
        return redirect("browse")
    return render(
        request,
        "matching/send_intro.html",
        {"recipient": recipient},
    )


@login_required
def accept_introduction(request, pk):
    intro = get_object_or_404(IntroductionRequest, pk=pk, recipient=request.user)
    if intro.status != IntroductionRequest.Status.PENDING:
        messages.error(request, "لا يمكن قبول هذا الطلب في حالته الحالية.")
        return redirect("intro_inbox")
    intro.status = IntroductionRequest.Status.PENDING_MODERATOR
    intro.save(update_fields=["status", "updated_at"])
    log_action(
        request.user,
        "intro_accepted_by_recipient",
        target_user=intro.requester,
        metadata={"intro_id": intro.pk},
    )
    messages.success(request, "تم القبول؛ الطلب أصبح بانتظار المشرف.")
    return redirect("intro_inbox")


@login_required
def intro_inbox(request):
    incoming = IntroductionRequest.objects.filter(recipient=request.user).select_related(
        "requester",
        "requester__applicant_profile",
    )
    outgoing = IntroductionRequest.objects.filter(requester=request.user).select_related(
        "recipient",
        "recipient__applicant_profile",
    )
    return render(
        request,
        "matching/inbox.html",
        {"incoming": incoming, "outgoing": outgoing},
    )
