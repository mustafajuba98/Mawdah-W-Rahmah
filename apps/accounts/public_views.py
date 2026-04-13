"""Public home / landing (guest) + authenticated dashboard."""

from __future__ import annotations

import logging

import requests
from django.views.generic import TemplateView

from services.landing_spiritual import build_spirit_cards

logger = logging.getLogger(__name__)

ALADHAN_TIMINGS_URL = "https://api.aladhan.com/v1/timingsByCity"

WHATSAPP_COMMUNITY_URL = (
    "https://chat.whatsapp.com/IF2rhhDw98h6W30pfjbBcP?mode=gi_t"
)
FACEBOOK_GROUP_URL = (
    "https://www.facebook.com/groups/1327870227876229/"
    "?ref=share_group_link&rdid=ylPngkRTd61XKNtL"
    "&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2Fg%2F1BPkwtpE7p%2F#"
)

# Cairo, Egypt — calculation method 5 (Egyptian General Authority)
PRAYER_QUERY = {"city": "Cairo", "country": "Egypt", "method": "5"}

PRAYER_ROWS_AR = (
    ("Fajr", "الفجر"),
    ("Sunrise", "الشروق"),
    ("Dhuhr", "الظهر"),
    ("Asr", "العصر"),
    ("Maghrib", "المغرب"),
    ("Isha", "العشاء"),
)


def fetch_prayer_timings_cairo() -> dict | None:
    """Returns {rows, hijri, gregorian} or None on failure."""
    try:
        r = requests.get(
            ALADHAN_TIMINGS_URL,
            params=PRAYER_QUERY,
            timeout=8,
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        payload = r.json()
        block = payload.get("data") or {}
        timings = block.get("timings") or {}
        date_info = block.get("date") or {}
        hijri = (date_info.get("hijri") or {}) if isinstance(date_info, dict) else {}
        greg = (date_info.get("gregorian") or {}) if isinstance(date_info, dict) else {}
        hijri_str = ""
        if isinstance(hijri, dict):
            hijri_str = hijri.get("date", "") or ""
        gregorian_str = ""
        if isinstance(greg, dict):
            gregorian_str = greg.get("readable", "") or greg.get("date", "") or ""

        rows = []
        for key, label_ar in PRAYER_ROWS_AR:
            t = timings.get(key)
            if t:
                rows.append({"label": label_ar, "time": t})

        return {
            "rows": rows,
            "hijri": hijri_str,
            "gregorian": gregorian_str,
        }
    except Exception as exc:
        logger.warning("Prayer timings fetch failed: %s", exc)
        return None


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
        ctx["prayer"] = fetch_prayer_timings_cairo()
        ctx["whatsapp_url"] = WHATSAPP_COMMUNITY_URL
        ctx["facebook_url"] = FACEBOOK_GROUP_URL
        ctx["spirit_cards"] = build_spirit_cards(target=6)
        return ctx
