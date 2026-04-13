"""Public home / landing (guest) + authenticated dashboard."""

from __future__ import annotations

from django.conf import settings
from django.templatetags.static import static
from django.views.generic import TemplateView

from services.landing_prayer import fetch_prayer_timings_cached
from services.landing_spiritual import build_spirit_cards

# دعوة مجموعة — بدون query params (أحياناً ?mode= يفتح واتساب ويب/تسجيل بدل التطبيق)
WHATSAPP_COMMUNITY_URL = "https://chat.whatsapp.com/IF2rhhDw98h6W30pfjbBcP"
FACEBOOK_GROUP_URL = (
    "https://www.facebook.com/groups/1327870227876229/"
    "?ref=share_group_link&rdid=ylPngkRTd61XKNtL"
    "&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2Fg%2F1BPkwtpE7p%2F#"
)


class HomeView(TemplateView):
    """Guests see the marketing landing; signed-in users see the app home."""

    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["home.html"]
        return ["landing.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            return ctx
        ctx["prayer"] = fetch_prayer_timings_cached()
        ctx["prayer_place"] = f"{settings.PRAYER_CITY}، {settings.PRAYER_COUNTRY}"
        ctx["whatsapp_url"] = WHATSAPP_COMMUNITY_URL
        ctx["facebook_url"] = FACEBOOK_GROUP_URL
        ctx["spirit_cards"] = build_spirit_cards(target=8)
        ctx["site_canonical"] = settings.SITE_CANONICAL_URL
        ctx["privacy_policy_url"] = settings.PRIVACY_POLICY_URL or None
        try:
            ctx["og_image_url"] = self.request.build_absolute_uri(
                static("img/brand-mosque.svg")
            )
        except Exception:
            ctx["og_image_url"] = ""
        return ctx
