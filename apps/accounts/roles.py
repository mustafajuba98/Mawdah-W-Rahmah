def is_moderation_portal_user(user) -> bool:
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(
        name__in=("platform_admin", "moderator")
    ).exists()


def show_member_site_nav(user) -> bool:
    """مشرف/أدمن بلا نوع مقدّم طلب: يخفى مسار العضو (استمارة/تصفح/…)."""
    if not user.is_authenticated:
        return False
    if is_moderation_portal_user(user) and not (user.applicant_gender or "").strip():
        return False
    return True
