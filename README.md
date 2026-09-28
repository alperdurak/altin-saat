# Altın Saat

BIST 100, USD/TRY ve gram altın fiyatlarını gösteren, Türkiye ve dünya ekonomisi haberlerini derleyen ve yapay zekâ destekli kısa bir Türkçe günlük bülten üreten Streamlit uygulaması.

## Özellikler

- **Koyu tema**: Renkler ve yazı tipi `.streamlit/config.toml` üzerinden tanımlanır.
- **Piyasa verisi**: BIST 100, USD/TRY ve gram altın (TRY) için gecikmeli güncel fiyat ve günlük yüzde değişim kartları (`yfinance`).
- **Haberler**: Türkiye ve dünya ekonomisi için 2'şer RSS kaynağından son başlıklar, sekmeler halinde ve tıklanabilir linklerle (`feedparser`).
- **Üst bar**: Son güncelleme saati (Türkiye saati) ve BIST seans durumu ("Seans açık" / "Seans kapalı") rozeti. Seans durumu, hafta içi 10:00–18:00 (Türkiye saati) kuralına dayanan **yaklaşık** bir göstergedir; resmi tatilleri hesaba katmaz.
- **AI bülten**: "Bülteni oluştur" butonuyla, haber başlıkları Claude API'ye (model: `claude-haiku-4-5-20251001`) gönderilir; model yapılandırılmış bir JSON döner (bölümler, madde başlığı/özeti, ilgili sektörler, kaynak linki). Uygulama bu JSON'dan:
  - Öne çıkan gelişmeleri, ilgili sektörleri renkli rozetler olarak ve kaynak linkleriyle gösterir,
  - Piyasa özeti satırını (BIST/USD/altın rakamları) doğrudan uygulamanın kendi verisinden hesaplar (model sayı üretmez),
  - `.md` formatında indirilebilir bir bülten dosyası üretir (`st.download_button`).
  
  Bülten kesinlikle al/sat gibi yatırım tavsiyesi içermez.

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

## Proje Yapısı

```
piyasa-bulteni/
├── app.py                  # Streamlit sayfası ve düzeni
├── bulletin.py              # Claude API ile bülten üretimi (JSON çıktı)
├── data.py                  # Piyasa verisi (yfinance) ve haber (RSS) çekme
├── ui.py                     # Tema/rozet yardımcıları ve tek yerde toplanan özel CSS
├── assets/
│   └── logo.svg              # Altın Saat logosu (şeffaf zemin)
├── docs/
│   └── tasarim.pdf           # Tasarım referansı
├── .streamlit/
│   └── config.toml           # Koyu tema renk ve font ayarları
├── requirements.txt
└── README.md
```

## Önemli Not

Bu uygulamanın ürettiği bülten ve gösterdiği veriler bilgilendirme amaçlıdır. **Bu içerik yatırım tavsiyesi değildir.** Piyasa verileri gecikmeli olabilir.

## Bilinen Sınırlamalar

- Gram altın fiyatı, doğrudan bir yfinance sembolü olmadığı için ons altın (USD) ve USD/TRY kurundan hesaplanan **yaklaşık gram has altın** değeridir; kuyumcu alış/satış fiyatından farklı olabilir.
- RSS kaynakları zaman içinde adres değiştirebilir veya geçici olarak erişilemez hale gelebilir.
- Piyasa verileri ve haberler kısa süreli (`st.cache_data`) önbelleğe alınır; sayfa her yenilendiğinde anlık en güncel veri garanti edilmez.
- "Seans açık/kapalı" rozeti sabit bir saat aralığına (hafta içi 10:00–18:00, Türkiye saati) dayanır; resmi tatiller ve seans dışı özel durumlar (yarım gün, ekstra kapanış vb.) hesaba katılmaz.
