# Piyasa Bülteni

BIST 100, USD/TRY ve gram altın fiyatlarını gösteren, Türkiye ve dünya ekonomisi haberlerini derleyen ve yapay zekâ destekli kısa bir Türkçe günlük bülten üreten Streamlit uygulaması.

## Özellikler

- **Piyasa verisi**: BIST 100, USD/TRY ve gram altın (TRY) için gecikmeli güncel fiyat ve günlük yüzde değişim kartları (`yfinance`).
- **Haberler**: Türkiye ve dünya ekonomisi için 2'şer RSS kaynağından son başlıklar, iki ayrı sütunda ve tıklanabilir linklerle (`feedparser`).
- **AI bülten**: "Bülteni oluştur" butonuyla, haber başlıkları Claude API'ye (model: `claude-haiku-4-5-20251001`) gönderilir ve öne çıkan gelişmeler, ilgili sektörler ve kaynak linkleriyle kısa bir Türkçe bülten üretilir. Bülten kesinlikle al/sat gibi yatırım tavsiyesi içermez.

## Gereksinimler

- Python 3.14 (veya üstü)
- Windows
- Bir Anthropic (Claude) API anahtarı

## Kurulum (Windows)

```powershell
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## API Anahtarı

Proje kök dizininde bir `.env` dosyası oluşturun (yoksa) ve içine şunu ekleyin:

```
ANTHROPIC_API_KEY=sk-ant-...
```

`.env` dosyası `.gitignore` içinde hariç tutulmuştur; bu dosyayı asla git'e eklemeyin veya başkalarıyla paylaşmayın.

## Çalıştırma

```powershell
streamlit run app.py
```

Uygulama varsayılan olarak `http://localhost:8501` adresinde açılır.

## Önemli Not

Bu uygulamanın ürettiği bülten ve gösterdiği veriler bilgilendirme amaçlıdır. **Bu içerik yatırım tavsiyesi değildir.** Piyasa verileri gecikmeli olabilir.

## Bilinen Sınırlamalar

- Gram altın fiyatı, doğrudan bir yfinance sembolü olmadığı için ons altın (USD) ve USD/TRY kurundan hesaplanan **yaklaşık gram has altın** değeridir; kuyumcu alış/satış fiyatından farklı olabilir.
- RSS kaynakları zaman içinde adres değiştirebilir veya geçici olarak erişilemez hale gelebilir.
- Piyasa verileri ve haberler kısa süreli (`st.cache_data`) önbelleğe alınır; sayfa her yenilendiğinde anlık en güncel veri garanti edilmez.
