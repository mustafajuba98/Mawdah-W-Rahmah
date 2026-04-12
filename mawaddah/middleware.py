from django.http import HttpResponseForbidden
from django.shortcuts import redirect


class SuperuserAdminOnlyMiddleware:
    """
    - Superusers are redirected from /admin/ to the in-app console (no Django admin UI).
    - Non-superusers get 403 on /admin/; staff moderation uses /moderation/.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""
        if path.startswith("/admin/"):
            u = request.user
            if u.is_authenticated and u.is_superuser:
                return redirect("/console/")
            if u.is_authenticated and not u.is_superuser:
                html = (
                    "<!DOCTYPE html><html lang='ar' dir='rtl'><head><meta charset='utf-8'>"
                    "<title>وصول مرفوض</title></head><body style='font-family:system-ui;padding:2rem;max-width:32rem'>"
                    "<h1>وصول مرفوض</h1>"
                    "<p>لوحة Django الإدارية (<code>/admin/</code>) غير متاحة لهذا الحساب.</p>"
                    "<p>استخدم <strong>لوحة الإشراف</strong> من القائمة الجانبية.</p>"
                    "</body></html>"
                )
                return HttpResponseForbidden(html, content_type="text/html; charset=utf-8")
        return self.get_response(request)
