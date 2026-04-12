def moderation_nav(request):
    u = request.user
    if not u.is_authenticated:
        return {"show_moderation_nav": False}
    show = u.is_superuser or u.groups.filter(
        name__in=("moderator", "platform_admin")
    ).exists()
    return {"show_moderation_nav": show}
