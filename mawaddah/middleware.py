from django.http import HttpResponseForbidden


class SuperuserAdminOnlyMiddleware:
    """
    يقيّد مسار Django Admin على السوبر يوزر فقط.
    المشرفون يستخدمون /moderation/ وليس /admin/.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""
        if path.startswith("/admin/"):
            u = request.user
            if u.is_authenticated and not u.is_superuser:
                html = (
                    "<!DOCTYPE html><html lang='ar' dir='rtl'><head><meta charset='utf-8'>"
                    "<title>وصول مرفوض</title></head><body style='font-family:system-ui;padding:2rem;max-width:32rem'>"
                    "<h1>وصول مرفوض</h1>"
                    "<p>لوحة Django الإدارية (<code>/admin/</code>) مخصّصة لمسؤول النظام (سوبر يوزر) فقط.</p>"
                    "<p>استخدم <strong>لوحة الإشراف</strong> من القائمة الجانبية لمهام المراجعة اليومية.</p>"
                    "</body></html>"
                )
                return HttpResponseForbidden(html, content_type="text/html; charset=utf-8")
        return self.get_response(request)
