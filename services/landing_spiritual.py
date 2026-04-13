"""Landing-page spiritual snippets: random ayahs (public API) + static adhkar pool."""

from __future__ import annotations

import logging
import secrets

import requests

logger = logging.getLogger(__name__)

ALQURAN_RANDOM_AYAH = "https://api.alquran.cloud/v1/ayah/random"

# Arabic editions via jsDelivr (fawazahmed0/hadith-api) — one JSON file = one «bundle» number.
HADITH_API_BASE = (
    "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
)
HADITH_BOOKS_MAX = (
    ("ara-bukhari", 7563),
    ("ara-muslim", 7000),
)

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


def _fetch_one_random_hadith() -> dict | None:
    """Random Arabic hadith from hadith-api CDN (Bukhari or Muslim)."""
    rng = secrets.SystemRandom()
    for _ in range(5):
        book, mx = rng.choice(HADITH_BOOKS_MAX)
        n = rng.randint(1, mx)
        url = f"{HADITH_API_BASE}/{book}/{n}.json"
        try:
            r = requests.get(url, timeout=12, headers={"Accept": "application/json"})
            if r.status_code != 200:
                continue
            data = r.json()
            hadiths = data.get("hadiths") or []
            if not hadiths:
                continue
            h = hadiths[0]
            text = (h.get("text") or "").strip()
            if len(text) < 20:
                continue
            meta = data.get("metadata") or {}
            book_ar = meta.get("name") or book.replace("ara-", "").title()
            ar_num = h.get("arabicnumber") or h.get("hadithnumber") or n
            short_book = "صحيح البخاري" if "bukhari" in book else "صحيح مسلم"
            return {
                "kind": "حديث",
                "title": f"{short_book} — حديث {ar_num}",
                "lines": [text],
                "source": (
                    f"النص من {book_ar} عبر مشروع hadith-api (jsDelivr) — راجع الروايات في المراجع الورقية."
                ),
            }
        except Exception as exc:
            logger.debug("Hadith fetch attempt failed: %s", exc)
            continue
    return None


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


def build_spirit_cards(*, target: int = 8) -> list[dict]:
    """Random ayah(s), one hadith when CDN responds, plus shuffled static adhkar."""
    cards: list[dict] = []
    seen: set[str] = set()

    def _add(card: dict) -> None:
        key = "|".join(card.get("lines") or [])[:240]
        if key in seen:
            return
        seen.add(key)
        cards.append(card)

    h = _fetch_one_random_hadith()
    if h:
        _add(h)

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

    secrets.SystemRandom().shuffle(cards)
    return cards[:target]
