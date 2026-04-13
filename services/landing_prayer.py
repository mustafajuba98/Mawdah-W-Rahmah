"""Prayer timings for landing (Aladhan) with in-process TTL cache."""

from __future__ import annotations

import logging
import threading
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ALADHAN_TIMINGS_URL = "https://api.aladhan.com/v1/timingsByCity"

PRAYER_ROWS_AR = (
    ("Fajr", "الفجر"),
    ("Sunrise", "الشروق"),
    ("Dhuhr", "الظهر"),
    ("Asr", "العصر"),
    ("Maghrib", "المغرب"),
    ("Isha", "العشاء"),
)

_lock = threading.Lock()
_cache: dict = {"key": "", "until": 0.0, "data": None}


def _calculation_method_for_country(country: str) -> int:
    """Egyptian authority method for Egypt; MWL elsewhere."""
    c = (country or "").strip().lower()
    if c in ("egypt", "eg", "مصر"):
        return 5
    return 3


def _fetch_prayer_timings_uncached(city: str, country: str) -> dict | None:
    try:
        r = requests.get(
            ALADHAN_TIMINGS_URL,
            params={
                "city": city,
                "country": country,
                "method": _calculation_method_for_country(country),
            },
            timeout=10,
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        payload = r.json()
        block = payload.get("data") or {}
        timings = block.get("timings") or {}
        date_info = block.get("date") or {}
        hijri = (date_info.get("hijri") or {}) if isinstance(date_info, dict) else {}
        greg = (date_info.get("gregorian") or {}) if isinstance(date_info, dict) else {}
        hijri_str = hijri.get("date", "") if isinstance(hijri, dict) else ""
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
            "city": city,
            "country": country,
        }
    except Exception as exc:
        logger.warning("Prayer timings fetch failed: %s", exc)
        return None


def fetch_prayer_timings_cached() -> dict | None:
    """Uses settings PRAYER_* and PRAYER_CACHE_SECONDS; thread-safe per-process cache."""
    city = settings.PRAYER_CITY
    country = settings.PRAYER_COUNTRY
    ttl = max(60, int(settings.PRAYER_CACHE_SECONDS))
    key = f"{city}|{country}"
    now = time.monotonic()
    with _lock:
        if (
            _cache["data"] is not None
            and _cache["key"] == key
            and now < _cache["until"]
        ):
            return _cache["data"]
    data = _fetch_prayer_timings_uncached(city, country)
    with _lock:
        _cache["key"] = key
        _cache["data"] = data
        _cache["until"] = now + float(ttl)
    return data
