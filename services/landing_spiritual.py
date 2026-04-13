"""Landing-page spiritual snippets: random ayahs (public API) + static adhkar pool."""

from __future__ import annotations

import logging
import secrets

import requests

logger = logging.getLogger(__name__)

ALQURAN_RANDOM_AYAH = "https://api.alquran.cloud/v1/ayah/random"

# Short authentic-style reminders (not a full Hisnul Muslim dump — point users to books).
_STATIC_POOL: list[dict] = [
    {
        "kind": "ذكر",
        "title": "تسبيح بعد الصلاة",
        "lines": [
            "سبحان الله والحمد لله والله أكبر — ثلاثاً وثلاثين بعد كل صلاة مكتوبة.",
        ],
        "source": "من السنة — راجع كتب الأذكار المعتمدة للأعداد والصيغ الدقيقة.",
    },
    {
        "kind": "ذكر",
        "title": "كفارة المجلس",
        "lines": [
            "سبحانك اللهم وبحمدك، أشهد أن لا إله إلا أنت، أستغفرك وأتوب إليك.",
        ],
        "source": "ثبت في الصحيحين عن أبي هريرة رضي الله عنه.",
    },
    {
        "kind": "ذكر",
        "title": "دخول المنزل",
        "lines": [
            "بسم الله ولجنا، وبسم الله خرجنا، وعلى الله ربنا توكلنا.",
        ],
        "source": "من أذكار الدخول والخروج — انظر الأذكار النبوية في المصادر المعتمدة.",
    },
    {
        "kind": "ذكر",
        "title": "الاستغفار",
        "lines": [
            "أستغفر الله العظيم الذي لا إله إلا هو الحي القيوم وأتوب إليه.",
        ],
        "source": "من الأذكار المأثورة؛ ردّدها بخشوع ومعرفة.",
    },
    {
        "kind": "ذكر",
        "title": "قبل النوم",
        "lines": [
            "باسمك اللهم أموت وأحيا.",
            "اللهم قني عذابك يوم تبعث عبادك.",
        ],
        "source": "من أذكار النوم في السنة.",
    },
    {
        "kind": "ذكر",
        "title": "عند الكرب",
        "lines": [
            "لا إله إلا أنت سبحانك إني كنت من الظالمين.",
        ],
        "source": "دعاء ذي النون عليه السلام — ثبت في السنة.",
    },
    {
        "kind": "ذكر",
        "title": "رِضا بالقدر",
        "lines": [
            "اللهم رضني بما قسمت لي حتى أرضى أن لا يكون لي إلا ما قسمت لي.",
        ],
        "source": "من أدعية التوفيق — راجع الأدعية المأثورة برواياتها.",
    },
    {
        "kind": "ذكر",
        "title": "بعد السلام من الصلاة",
        "lines": [
            "أستغفر الله، أستغفر الله، أستغفر الله.",
            "اللهم أنت السلام ومنك السلام تباركت يا ذا الجلال والإكرام.",
        ],
        "source": "من أذكار ما بعد السلام — بصيغها في الكتب المعتمدة.",
    },
    {
        "kind": "ذكر",
        "title": "كثرة الصلاة على النبي ﷺ",
        "lines": [
            "اللهم صلّ على محمد وعلى آل محمد، كما صلّيت على إبراهيم وعلى آل إبراهيم…",
        ],
        "source": "الصلاة الإبراهيمية بعد التشهد — برواياتها في الحديث.",
    },
    {
        "kind": "ذكر",
        "title": "دخول المسجد",
        "lines": [
            "بسم الله، والصلاة والسلام على رسول الله، اللهم اغفر لي ذنوبي وافتح لي أبواب رحمتك.",
        ],
        "source": "من أذكار دخول المسجد — راجع الروايات في الأذكار النبوية.",
    },
]


def _fetch_one_random_ayah() -> dict | None:
    try:
        r = requests.get(ALQURAN_RANDOM_AYAH, timeout=8, headers={"Accept": "application/json"})
        r.raise_for_status()
        body = r.json()
        d = body.get("data") or {}
        text = (d.get("text") or "").strip()
        if not text:
            return None
        surah = d.get("surah") or {}
        name = surah.get("name", "") if isinstance(surah, dict) else ""
        title = f"سورة {name}" if name else "من القرآن الكريم"
        return {
            "kind": "آية",
            "title": title,
            "lines": [text],
            "source": "نص عشوائي من خدمة api.alquran.cloud — راجع المصحف للضبط.",
        }
    except Exception as exc:
        logger.debug("Random ayah fetch skipped: %s", exc)
        return None


def build_spirit_cards(*, target: int = 6) -> list[dict]:
    """Mix random ayahs (when API works) with shuffled static adhkar; few repeats per page load."""
    cards: list[dict] = []
    seen = set()

    def _add(card: dict) -> None:
        key = "|".join(card.get("lines") or [])[:200]
        if key in seen:
            return
        seen.add(key)
        cards.append(card)

    for _ in range(2):
        if len(cards) >= target:
            break
        ayah = _fetch_one_random_ayah()
        if ayah:
            _add(ayah)

    order = list(_STATIC_POOL)
    secrets.SystemRandom().shuffle(order)
    for item in order:
        if len(cards) >= target:
            break
        _add(item)

    return cards[:target]
