from apps.accounts.models import User
from apps.matching.models import IntroductionRequest
from apps.profiles.models import ApplicantProfile


def _staff_like(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name__in=("platform_admin", "moderator")).exists()
    )


def can_view_profile_browse(viewer, target_user):
    """بطاقة التصفح: ملفات مفعّلة فقط، الجنس المقابل، ليس نفس المستخدم."""
    if not viewer.is_authenticated:
        return False
    if viewer.pk == target_user.pk:
        return False
    if viewer.profile_status != User.ProfileStatus.ACTIVE:
        return False
    if target_user.profile_status != User.ProfileStatus.ACTIVE:
        return False
    vp = ApplicantProfile.objects.filter(user=viewer).first()
    tp = ApplicantProfile.objects.filter(user=target_user).first()
    if not vp or not tp:
        return False
    if vp.applicant_gender == tp.applicant_gender:
        return False
    return True


def can_view_full_profile(viewer, target_user):
    """الاستمارة كاملة: صاحب الملف، الطاقم، أو بعد موافقة المشرف على الطلب."""
    if not viewer.is_authenticated:
        return False
    if viewer.pk == target_user.pk:
        return True
    if _staff_like(viewer):
        return True
    return IntroductionRequest.objects.filter(
        status=IntroductionRequest.Status.APPROVED,
        requester=viewer,
        recipient=target_user,
    ).exists() or IntroductionRequest.objects.filter(
        status=IntroductionRequest.Status.APPROVED,
        requester=target_user,
        recipient=viewer,
    ).exists()


def can_view_contact_details(viewer, target_user):
    """بيانات التواصل بعد نفس بوابة الملف الكامل."""
    return can_view_full_profile(viewer, target_user)


def can_view_intro_requester_preview(viewer, target_user):
    """
    المستلم لطلب رؤية معلّق (بانتظار قبوله) يرى ملخصاً أوضح عن مقدّم الطلب
    لاتخاذ قرار القبول — دون بيانات تواصل حتى موافقة المشرف.
    """
    if not viewer.is_authenticated:
        return False
    return IntroductionRequest.objects.filter(
        requester=target_user,
        recipient=viewer,
        status=IntroductionRequest.Status.PENDING,
    ).exists()


def log_profile_view(audit_model, viewer, target_user, detail_level, request):
    if not viewer.is_authenticated or viewer.pk == target_user.pk:
        return
    ip = request.META.get("REMOTE_ADDR", "") if request else ""
    audit_model.objects.create(
        actor=viewer,
        action="profile_view",
        target_user=target_user,
        metadata={"detail_level": detail_level, "ip": ip},
    )
