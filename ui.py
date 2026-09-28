"""Altın Saat için tema-bağımlı görünüm yardımcıları.

Rozetler (seans durumu, sektör etiketleri, küçük etiketler) için gereken
özel CSS burada tek bir yerde toplanır; diğer tüm renklendirme (metric
delta'ları, buton, tab, container çerçevesi) .streamlit/config.toml
temasından otomatik gelir.
"""
import zlib
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

TR_TZ = ZoneInfo("Europe/Istanbul")

_MONTHS_TR = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]
_WEEKDAYS_TR = [
    "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar",
]

_SECTOR_PALETTE = [
    ("rgba(59, 130, 246, .15)", "#60a5fa"),   # mavi
    ("rgba(168, 85, 247, .15)", "#c084fc"),   # mor
    ("rgba(236, 72, 153, .15)", "#f472b6"),   # pembe
    ("rgba(20, 184, 166, .15)", "#2dd4bf"),   # turkuaz
    ("rgba(99, 102, 241, .15)", "#818cf8"),   # indigo
    ("rgba(249, 115, 22, .15)", "#fb923c"),   # turuncu
    ("rgba(6, 182, 212, .15)", "#22d3ee"),    # camgöbeği
    ("rgba(217, 70, 239, .15)", "#e879f9"),   # fuşya
]


def inject_css() -> None:
    """Sayfa başında bir kez çağrılır; tüm özel CSS burada toplanır."""
    st.markdown(
        """
        <style>
        .as-badge {
            display: inline-flex;
            align-items: center;
            gap: .35rem;
            padding: .2rem .7rem;
            border-radius: 999px;
            font-size: .8rem;
            font-weight: 600;
            white-space: nowrap;
        }
        .as-badge-open { background: rgba(34, 197, 94, .15); color: #4ade80; }
        .as-badge-closed { background: rgba(248, 113, 113, .15); color: #f87171; }
        .as-tag {
            font-size: .65rem;
            text-transform: uppercase;
            letter-spacing: .04em;
            color: #9aa5b8;
            background: rgba(255, 255, 255, .06);
            padding: .1rem .5rem;
            border-radius: 6px;
        }
        .as-sector {
            display: inline-block;
            padding: .15rem .6rem;
            border-radius: 999px;
            font-size: .75rem;
            font-weight: 500;
            margin: .15rem .3rem .15rem 0;
        }
        .as-logo svg {
            width: 100%;
            height: 100%;
            display: block;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def session_status() -> tuple[str, str]:
    """Türkiye saatiyle hafta içi 10:00-18:00 aralığına göre seans durumu.

    Resmi tatilleri hesaba katmayan yaklaşık bir kuraldır.
    """
    now = datetime.now(TR_TZ)
    is_weekday = now.weekday() < 5
    is_session_hours = 10 <= now.hour < 18
    if is_weekday and is_session_hours:
        return "Seans açık", "open"
    return "Seans kapalı", "closed"


def format_update_time() -> str:
    return datetime.now(TR_TZ).strftime("%H:%M")


def format_tr_date(dt: datetime) -> str:
    return f"{dt.day} {_MONTHS_TR[dt.month - 1].upper()} {dt.year}, {_WEEKDAYS_TR[dt.weekday()].upper()}"


def format_tr_number(value: float, decimals: int = 2) -> str:
    """`12.899,40` biçimi: binlik ayraç nokta, ondalık ayraç virgül."""
    formatted = f"{value:,.{decimals}f}"
    formatted = formatted.replace(",", "\0").replace(".", ",").replace("\0", ".")
    return formatted


def format_tr_pct(value: float) -> str:
    sign = "+" if value >= 0 else "-"
    return f"{sign}%{format_tr_number(abs(value))}"


def session_badge_html(label: str, state: str) -> str:
    css_class = "as-badge-open" if state == "open" else "as-badge-closed"
    return f'<span class="as-badge {css_class}">● {label}</span>'


def tag_html(text: str) -> str:
    return f'<span class="as-tag">{text}</span>'


def sector_badge_html(sectors: list[str]) -> str:
    spans = []
    for sector in sectors:
        idx = zlib.crc32(sector.encode("utf-8")) % len(_SECTOR_PALETTE)
        bg, fg = _SECTOR_PALETTE[idx]
        spans.append(
            f'<span class="as-sector" style="background:{bg};color:{fg}">{sector}</span>'
        )
    return "".join(spans)
