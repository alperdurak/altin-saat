"""Claude API ile Türkçe günlük bülten üretimi (yapılandırılmış JSON çıktı)."""
import json
import os
import re

from anthropic import Anthropic
from dotenv import load_dotenv

from data import Headline

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """\
Sen bir piyasa bülteni asistanısın. Sana verilen günün piyasa rakamlarından \
ve Türkiye/dünya ekonomisi haber başlıklarından kısa, Türkçe bir günlük \
bülten hazırlıyorsun.

BÖLÜMLENDİRME: Kullanıcı mesajındaki "TÜRKİYE EKONOMİSİ" ve "DÜNYA \
EKONOMİSİ" başlıkları altındaki gruplamalar, haberin hangi RSS \
kaynağından çekildiğini gösterir; haberin konusunu göstermez. Bültende \
haberleri bu ham gruplamaya göre değil, içeriğine göre doğru bölüme \
yerleştir: TCMB kararları, enflasyon, döviz kuru, Türk şirketleri, BIST \
gibi doğrudan Türkiye ekonomisini ilgilendiren gelişmeleri Türkiye \
Ekonomisi bölümüne yaz; Fed, petrol, küresel şirketler, uluslararası \
piyasalar gibi gelişmeleri, hangi kaynaktan geldiğine bakılmaksızın Dünya \
Ekonomisi bölümüne yaz.

HABER SEÇİMİ: Her bölümden (Türkiye ekonomisi / dünya ekonomisi) piyasalar \
için gerçekten önemli olan en fazla 3-4 haberi seç: faiz kararları, \
enflasyon verileri, döviz kuru hareketleri, emtia fiyatları, büyük şirket \
haberleri ve bir sektörü geniş çapta etkileyebilecek gelişmeler. Yerel \
fiyat denetimi, tek bir şirketteki yönetici ataması gibi piyasa etkisi \
düşük haberleri atla. Bir bölümde piyasalar açısından gerçekten önemli \
hiçbir haber yoksa o bölümün "items" dizisini boş bırak; zorla haber \
seçme ve o bölüm için ayrıca bir açıklama cümlesi yazma.

MADDE İÇERİĞİ: Her madde için:
- "title": haberin kısa özeti (kalın başlık olarak gösterilecek).
- "body": en fazla iki cümle: (1) ne oldu, (2) piyasalar için neden önemli \
olabileceği. "Takip edilmektedir", "devam etmektedir", "gözlemlenmektedir" \
gibi bilgi taşımayan dolgu cümleler kullanma. Başlıkta yer almayan hiçbir \
bilgiyi uydurma. Etki hakkındaki yorumlarda "olabilir", "etkileyebilir" \
gibi temkinli bir dil kullan, kesin iddialarda bulunma.
- "sectors": haberle ilgili 1-3 kısa sektör/etiket adından oluşan bir dizi \
(ör. ["Bankacılık", "Finans"]).
- "source_link": sana verilen link, olduğu gibi (uydurma).

ÇIKTI FORMATI: Yanıtın SADECE aşağıdaki şemaya uyan geçerli bir JSON nesnesi \
olsun; JSON dışında hiçbir metin, açıklama veya kod bloğu işareti ekleme:
{
  "sections": [
    {"name": "DÜNYA EKONOMİSİ", "items": [{"title": "...", "body": "...", "sectors": ["..."], "source_link": "..."}]},
    {"name": "TÜRKİYE EKONOMİSİ", "items": [...]}
  ]
}

ÇOK ÖNEMLİ KURAL: Kesinlikle "al", "sat", "elinde tut", "yatır" gibi \
yatırım tavsiyesi niteliğinde hiçbir ifade kullanma. Sadece nötr ve \
bilgilendirici bir dille yaz; okuyucuya ne yapması gerektiğini söyleme. \
Sadece sana verilen başlıkları ve rakamları kullan, kaynak veya bilgi \
uydurma.
"""


def _client() -> Anthropic | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic()


def build_user_message(
    tr_headlines: list[Headline],
    world_headlines: list[Headline],
) -> str:
    lines = ["TÜRKİYE EKONOMİSİ:"]
    if tr_headlines:
        for i, h in enumerate(tr_headlines, start=1):
            lines.append(f"{i}. [{h.source}] {h.title} — {h.link}")
    else:
        lines.append("(başlık yok)")

    lines.append("")
    lines.append("DÜNYA EKONOMİSİ:")
    if world_headlines:
        for i, h in enumerate(world_headlines, start=1):
            lines.append(f"{i}. [{h.source}] {h.title} — {h.link}")
    else:
        lines.append("(başlık yok)")

    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    stripped = text.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*)```\s*$", stripped, re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1).strip()
    return json.loads(stripped)


def generate_bulletin(
    tr_headlines: list[Headline],
    world_headlines: list[Headline],
) -> tuple[dict | None, str | None, bool]:
    """Bülten JSON'unu, varsa hata mesajını ve kesilip kesilmediğini döner."""
    if not tr_headlines and not world_headlines:
        return None, "Şu anda gösterilecek haber başlığı bulunamadı.", False

    client = _client()
    if client is None:
        return None, "ANTHROPIC_API_KEY bulunamadı. Lütfen .env dosyasını kontrol edin.", False

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=3000,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": build_user_message(tr_headlines, world_headlines),
            }],
        )
        truncated = response.stop_reason == "max_tokens"
        if truncated:
            return None, "Bülten uzunluk sınırı nedeniyle oluşturulamadı. Lütfen tekrar deneyin.", True

        bulletin_json = _extract_json(response.content[0].text)
        return bulletin_json, None, False
    except json.JSONDecodeError:
        return None, "Bülten oluşturulurken bir biçim hatası oluştu. Lütfen tekrar deneyin.", False
    except Exception as e:
        print(f"[bulletin] Claude API hatası: {type(e).__name__}")
        return None, "Bülten oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.", False


def bulletin_to_markdown(bulletin_json: dict, summary_line: str, date_str: str) -> str:
    """Bülten JSON'unu .md indirme butonu için düz metin markdown'a çevirir."""
    lines = [f"# Piyasalarda günün özeti", "", date_str, "", summary_line, ""]

    for section in bulletin_json.get("sections", []):
        lines.append(f"## {section['name']}")
        lines.append("")
        items = section.get("items", [])
        if not items:
            lines.append("Bugün bu alanda öne çıkan bir piyasa gelişmesi yok.")
            lines.append("")
            continue
        for item in items:
            lines.append(f"**{item['title']}**")
            lines.append("")
            lines.append(item["body"])
            lines.append("")
            sectors = item.get("sectors", [])
            if sectors:
                lines.append(f"İlgili sektörler: {', '.join(sectors)}")
                lines.append("")
            if item.get("source_link"):
                lines.append(f"Kaynak: {item['source_link']}")
                lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Bu içerik yatırım tavsiyesi değildir. Veriler gecikmeli olabilir.")
    return "\n".join(lines)
