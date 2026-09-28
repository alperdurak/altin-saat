"""Piyasa verisi (yfinance) ve haber (RSS) çekme fonksiyonları."""
from dataclasses import dataclass

import feedparser
import streamlit as st
import yfinance as yf

TROY_OUNCE_IN_GRAMS = 31.1034768

TURKEY_NEWS_FEEDS = [
    ("AA Ekonomi", "https://www.aa.com.tr/tr/rss/default?cat=ekonomi"),
    ("NTV Ekonomi", "https://www.ntv.com.tr/ekonomi.rss"),
]

WORLD_NEWS_FEEDS = [
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("CNBC World Economy", "https://www.cnbc.com/id/100727362/device/rss/rss.html"),
]


def _safe_last_price_and_change(ticker: str) -> tuple[float | None, float | None]:
    """Bir yfinance ticker'ı için (son fiyat, günlük yüzde değişim) döner.

    Veri alınamazsa (ağ hatası, geçersiz sembol, boş veri) exception
    fırlatmadan (None, None) döner; çağıran taraf bunu hata olarak yorumlar.
    """
    try:
        hist = yf.Ticker(ticker).history(period="2d")
        if len(hist) < 2:
            return None, None
        prev_close = hist["Close"].iloc[-2]
        last_close = hist["Close"].iloc[-1]
        change_pct = (last_close - prev_close) / prev_close * 100
        return float(last_close), float(change_pct)
    except Exception:
        return None, None


@st.cache_data(ttl=90)
def get_bist100() -> dict:
    price, change_pct = _safe_last_price_and_change("XU100.IS")
    return {
        "label": "BIST 100",
        "price": price,
        "change_pct": change_pct,
        "error": None if price is not None else "Veri alınamadı",
    }


@st.cache_data(ttl=90)
def get_usdtry() -> dict:
    price, change_pct = _safe_last_price_and_change("USDTRY=X")
    return {
        "label": "USD/TRY",
        "price": price,
        "change_pct": change_pct,
        "error": None if price is not None else "Veri alınamadı",
    }


def _gold_usd_per_ounce() -> tuple[float | None, float | None]:
    price, change_pct = _safe_last_price_and_change("GC=F")
    if price is None:
        price, change_pct = _safe_last_price_and_change("XAUUSD=X")
    return price, change_pct


@st.cache_data(ttl=90)
def get_gram_gold_try() -> dict:
    """Gram has altın (yaklaşık) fiyatını TL cinsinden hesaplar.

    yfinance'ta doğrudan gram altın/TL sembolü olmadığı için ons altın (USD)
    ve USD/TRY kurundan türetilir. Bu, kuyumcu alış/satış fiyatı değil,
    yaklaşık bir spot değerdir.
    """
    gold_usd, gold_change_pct = _gold_usd_per_ounce()
    usdtry_data = get_usdtry()
    usdtry_price = usdtry_data["price"]

    if gold_usd is None or usdtry_price is None:
        return {
            "label": "Gram Altın (TRY)",
            "price": None,
            "change_pct": None,
            "error": "Veri alınamadı",
        }

    gram_price = gold_usd / TROY_OUNCE_IN_GRAMS * usdtry_price
    # Değişim yüzdesini basitleştirmek için ons altının kendi günlük
    # değişimini kullanıyoruz (kur değişimi görece küçük ve gürültülü).
    return {
        "label": "Gram Altın (TRY)",
        "price": gram_price,
        "change_pct": gold_change_pct,
        "error": None,
    }


@dataclass
class Headline:
    title: str
    link: str
    source: str
    published: str | None


def _parse_feed(url: str, source_name: str, limit: int = 4) -> list[Headline]:
    try:
        feed = feedparser.parse(url)
        headlines = []
        for entry in feed.entries[:limit]:
            headlines.append(
                Headline(
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    source=source_name,
                    published=entry.get("published") or entry.get("updated"),
                )
            )
        return headlines
    except Exception:
        return []


def take_per_source(headlines: list[Headline], limit: int) -> list[Headline]:
    """Her kaynaktan en fazla `limit` başlık alır, orijinal sırayı korur.

    Sayfada gösterim için, bültene giden geniş havuzdan dengeli bir alt küme
    seçmek amacıyla kullanılır (aksi halde ilk kaynağın başlıkları listeye
    hakim olur).
    """
    counts: dict[str, int] = {}
    result = []
    for h in headlines:
        if counts.get(h.source, 0) < limit:
            result.append(h)
            counts[h.source] = counts.get(h.source, 0) + 1
    return result


@st.cache_data(ttl=120)
def get_turkey_economy_news(limit_per_source: int = 10) -> list[Headline]:
    """Kaynak başına `limit_per_source` başlık döner (bülten için geniş havuz).

    Sayfada gösterilecek başlık sayısı ayrıdır; çağıran taraf listeyi kırpar.
    """
    headlines = []
    for source_name, url in TURKEY_NEWS_FEEDS:
        headlines.extend(_parse_feed(url, source_name, limit=limit_per_source))
    return headlines


@st.cache_data(ttl=120)
def get_world_economy_news(limit_per_source: int = 10) -> list[Headline]:
    """Kaynak başına `limit_per_source` başlık döner (bülten için geniş havuz).

    Sayfada gösterilecek başlık sayısı ayrıdır; çağıran taraf listeyi kırpar.
    """
    headlines = []
    for source_name, url in WORLD_NEWS_FEEDS:
        headlines.extend(_parse_feed(url, source_name, limit=limit_per_source))
    return headlines
