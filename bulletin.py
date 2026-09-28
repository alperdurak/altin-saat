"""Claude API ile Türkçe günlük bülten üretimi."""
import os

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

BÜLTENİN İLK SATIRI: Sana verilen BIST 100, USD/TRY ve gram altın \
rakamlarını ve günlük yüzde değişimlerini özetleyen tek bir cümle yaz. Bu \
cümle, herhangi bir başlıktan önce, bülten metninin en başında yer alsın.

HABER SEÇİMİ: Her bölümden (Türkiye ekonomisi / dünya ekonomisi) piyasalar \
için gerçekten önemli olan en fazla 3-4 haberi seç: faiz kararları, \
enflasyon verileri, döviz kuru hareketleri, emtia fiyatları, büyük şirket \
haberleri ve bir sektörü geniş çapta etkileyebilecek gelişmeler. Yerel \
fiyat denetimi, tek bir şirketteki yönetici ataması gibi piyasa etkisi \
düşük haberleri atla. Bir bölümde piyasalar açısından gerçekten önemli \
hiçbir haber yoksa o bölüm için zorla haber seçme; bunun yerine o bölüme \
sadece şu cümleyi yaz: "Bugün bu alanda öne çıkan bir piyasa gelişmesi \
yok."

MADDE FORMATI: Her madde şu şekilde olsun:
- **Kalın başlık** (haberin kısa özeti)
- En fazla iki cümle: (1) ne oldu, (2) piyasalar için neden önemli \
olabileceği. "Takip edilmektedir", "devam etmektedir", "gözlemlenmektedir" \
gibi bilgi taşımayan dolgu cümleler kullanma. Başlıkta yer almayan hiçbir \
bilgiyi uydurma. Etki hakkındaki yorumlarda "olabilir", "etkileyebilir" \
gibi temkinli bir dil kullan, kesin iddialarda bulunma.
- "İlgili sektörler: ..." etiketli bir satır.
- Kaynak bağlantısı (sana verilen link, olduğu gibi).

Çıktıyı Markdown olarak biçimlendir ki linkler tıklanabilir olsun.

ÇOK ÖNEMLİ KURAL: Kesinlikle "al", "sat", "elinde tut", "yatır" gibi \
yatırım tavsiyesi niteliğinde hiçbir ifade kullanma. Sadece nötr ve \
bilgilendirici bir dille yaz; okuyucuya ne yapması gerektiğini söyleme. \
Sadece sana verilen başlıkları ve rakamları kullan, kaynak veya bilgi \
uydurma. Bir kategoride hiç başlık yoksa bunu kısaca belirt.
"""


def _client() -> Anthropic | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic()


def _format_market_data(market_data: list[dict]) -> str:
    lines = ["GÜNÜN RAKAMLARI:"]
    for d in market_data:
        if d.get("error"):
            continue
        lines.append(f"- {d['label']}: {d['price']:.2f} ({d['change_pct']:+.2f}%)")
    return "\n".join(lines)


def build_user_message(
    market_data: list[dict],
    tr_headlines: list[Headline],
    world_headlines: list[Headline],
) -> str:
    lines = [_format_market_data(market_data), ""]

    lines.append("TÜRKİYE EKONOMİSİ:")
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


def generate_bulletin(
    market_data: list[dict],
    tr_headlines: list[Headline],
    world_headlines: list[Headline],
) -> tuple[str, bool]:
    """Bülten metnini ve max_tokens nedeniyle kesilip kesilmediğini döner."""
    if not tr_headlines and not world_headlines:
        return "Şu anda gösterilecek haber başlığı bulunamadı.", False

    client = _client()
    if client is None:
        return "ANTHROPIC_API_KEY bulunamadı. Lütfen .env dosyasını kontrol edin.", False

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": build_user_message(market_data, tr_headlines, world_headlines),
            }],
        )
        truncated = response.stop_reason == "max_tokens"
        return response.content[0].text, truncated
    except Exception as e:
        print(f"[bulletin] Claude API hatası: {type(e).__name__}")
        return "Bülten oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.", False
