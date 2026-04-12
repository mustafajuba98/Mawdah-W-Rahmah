from apps.accounts.roles import is_moderation_portal_user, show_member_site_nav


def moderation_nav(request):
    u = request.user
    if not u.is_authenticated:
        return {
            "show_moderation_nav": False,
            "show_member_site_nav": False,
        }
    return {
        "show_moderation_nav": is_moderation_portal_user(u),
        "show_member_site_nav": show_member_site_nav(u),
    }
