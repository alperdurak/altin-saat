"""Piyasa Bülteni - Streamlit uygulaması."""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import bulletin
import data

st.set_page_config(page_title="Piyasa Bülteni", page_icon="📊", layout="wide")
st.title("📊 Piyasa Bülteni")

# --- 1. Piyasa verisi kartları ---
col1, col2, col3 = st.columns(3)
market_data = [data.get_bist100(), data.get_usdtry(), data.get_gram_gold_try()]

for col, d in zip((col1, col2, col3), market_data):
    with col:
        if d["error"]:
            st.warning(f"{d['label']}: {d['error']}")
        else:
            st.metric(d["label"], f"{d['price']:.2f}", f"{d['change_pct']:+.2f}%")

st.caption("Gram Altın (TRY) değeri, ons altın (USD) ve USD/TRY kurundan hesaplanan yaklaşık gram has altın fiyatıdır.")

st.divider()

# --- 2. Haberler ---
st.subheader("Haberler")
news_col1, news_col2 = st.columns(2)

tr_news = data.get_turkey_economy_news()
world_news = data.get_world_economy_news()

with news_col1:
    st.markdown("**Türkiye Ekonomisi**")
    tr_news_display = data.take_per_source(tr_news, 4)
    if tr_news_display:
        for h in tr_news_display:
            st.markdown(f"- [{h.title}]({h.link})  \n  _{h.source}_")
    else:
        st.caption("Şu anda haber bulunamadı.")

with news_col2:
    st.markdown("**Dünya Ekonomisi**")
    world_news_display = data.take_per_source(world_news, 4)
    if world_news_display:
        for h in world_news_display:
            st.markdown(f"- [{h.title}]({h.link})  \n  _{h.source}_")
    else:
        st.caption("Şu anda haber bulunamadı.")

st.divider()

# --- 3. AI bülten ---
if st.button("Bülteni oluştur"):
    with st.spinner("Bülten oluşturuluyor..."):
        text, truncated = bulletin.generate_bulletin(market_data, tr_news, world_news)
        st.session_state["bulletin_text"] = text
        st.session_state["bulletin_truncated"] = truncated

if "bulletin_text" in st.session_state:
    st.markdown(st.session_state["bulletin_text"])
    if st.session_state.get("bulletin_truncated"):
        st.warning("Bülten uzunluk sınırı nedeniyle kısaltıldı.")

# --- 4. Uyarı ---
st.divider()
st.caption("⚠️ Bu içerik yatırım tavsiyesi değildir.")
