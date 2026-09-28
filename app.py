"""Altın Saat - Streamlit uygulaması."""
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import bulletin
import data
import ui

LOGO_SVG = Path("assets/logo.svg").read_text(encoding="utf-8")

st.set_page_config(
    page_title="Altın Saat",
    page_icon="🕰️",
    layout="wide",
)
ui.inject_css()

# --- 0. Üst bar ---
top_left, top_right = st.columns([3, 1])

with top_left:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:.6rem;">'
        f'<div class="as-logo" style="height:48px;width:48px;flex-shrink:0;">{LOGO_SVG}</div>'
        f'<div>'
        f'<div style="font-size:1.4rem;font-weight:700;line-height:1.2;">Altın Saat</div>'
        f'<div style="font-size:.85rem;color:#9aa5b8;line-height:1.2;">Günlük piyasa bülteni</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

with top_right:
    session_label, session_state = ui.session_status()
    st.markdown(
        f'<div style="text-align:right;">'
        f'<span style="color:#9aa5b8;font-size:.85rem;">Son güncelleme: {ui.format_update_time()}</span>'
        f'&nbsp;&nbsp;{ui.session_badge_html(session_label, session_state)}'
        f'</div>',
        unsafe_allow_html=True,
    )

st.divider()

# --- 1. Piyasa verisi kartları ---
col1, col2, col3 = st.columns(3)
market_data = [data.get_bist100(), data.get_usdtry(), data.get_gram_gold_try()]

for col, d in zip((col1, col2, col3), market_data):
    with col:
        with st.container(border=True):
            if d["error"]:
                st.warning(f"{d['label']}: {d['error']}")
            else:
                label = d["label"]
                if label == "Gram Altın (TRY)":
                    st.markdown(
                        f'<div style="font-size:.875rem;color:#9aa5b8;">'
                        f'{label} {ui.tag_html("yaklaşık değer")}</div>',
                        unsafe_allow_html=True,
                    )
                    st.metric(label, ui.format_tr_number(d["price"]), ui.format_tr_pct(d["change_pct"]), label_visibility="collapsed")
                else:
                    st.metric(label, ui.format_tr_number(d["price"]), ui.format_tr_pct(d["change_pct"]))

st.caption("Gram Altın (TRY) değeri, ons altın (USD) ve USD/TRY kurundan hesaplanan yaklaşık gram has altın fiyatıdır.")

st.divider()

# --- 2. Haberler ---
st.subheader("Haberler", anchor=False)

tr_news = data.get_turkey_economy_news()
world_news = data.get_world_economy_news()

with st.container(border=True):
    tab_tr, tab_world = st.tabs(["Türkiye", "Dünya"])

    with tab_tr:
        tr_news_display = data.take_per_source(tr_news, 4)
        if tr_news_display:
            for h in tr_news_display:
                st.markdown(f"- [{h.title}]({h.link})  \n  _{h.source}_")
        else:
            st.caption("Şu anda haber bulunamadı.")

    with tab_world:
        world_news_display = data.take_per_source(world_news, 4)
        if world_news_display:
            for h in world_news_display:
                st.markdown(f"- [{h.title}]({h.link})  \n  _{h.source}_")
        else:
            st.caption("Şu anda haber bulunamadı.")

st.divider()

# --- 3. AI bülten ---
st.subheader("Günlük bülten", anchor=False)
st.caption("Yapay zekâ, güncel haberlerden ve piyasa verilerinden kısa bir özet hazırlar.")

if st.button("Bülteni oluştur", type="primary"):
    with st.spinner("Bülten oluşturuluyor..."):
        bulletin_json, error, truncated = bulletin.generate_bulletin(tr_news, world_news)
        st.session_state["bulletin_json"] = bulletin_json
        st.session_state["bulletin_error"] = error
        st.session_state["bulletin_truncated"] = truncated
        st.session_state["bulletin_market_data"] = market_data
        st.session_state["bulletin_generated_at"] = datetime.now(ui.TR_TZ)

if "bulletin_json" in st.session_state:
    error = st.session_state.get("bulletin_error")
    bulletin_json = st.session_state.get("bulletin_json")

    if error:
        if error == "Şu anda gösterilecek haber başlığı bulunamadı.":
            st.info(error)
        else:
            st.error(error)
    elif bulletin_json:
        generated_at = st.session_state["bulletin_generated_at"]
        bulletin_market_data = st.session_state["bulletin_market_data"]
        date_str = ui.format_tr_date(generated_at)

        summary_parts = []
        for d in bulletin_market_data:
            if d["error"]:
                continue
            summary_parts.append(
                f"{d['label']} {ui.format_tr_number(d['price'])} ({ui.format_tr_pct(d['change_pct'])})"
            )
        summary_line = " · ".join(summary_parts)

        md_content = bulletin.bulletin_to_markdown(bulletin_json, summary_line, date_str)

        with st.container(border=True):
            header_col, download_col = st.columns([4, 1])
            with header_col:
                st.caption(date_str)
                st.markdown(
                    '<div style="font-size:1.15rem;font-weight:700;">Piyasalarda günün özeti</div>',
                    unsafe_allow_html=True,
                )
            with download_col:
                st.download_button(
                    "⬇️ İndir",
                    data=md_content,
                    file_name=f"altin-saat-bulteni-{generated_at.strftime('%Y-%m-%d')}.md",
                    mime="text/markdown",
                )

            if summary_line:
                with st.container(border=True):
                    st.markdown(summary_line)

            for section in bulletin_json.get("sections", []):
                st.caption(section["name"])
                items = section.get("items", [])
                if not items:
                    st.caption("Bugün bu alanda öne çıkan bir piyasa gelişmesi yok.")
                else:
                    for item in items:
                        st.markdown(f"**{item['title']}**")
                        st.write(item["body"])
                        sectors = item.get("sectors", [])
                        if sectors:
                            st.markdown(ui.sector_badge_html(sectors), unsafe_allow_html=True)
                        if item.get("source_link"):
                            st.markdown(f"[Kaynak ↗]({item['source_link']})")
                        st.divider()

# --- 4. Uyarı ---
st.divider()
st.caption(f"⚠️ Bu içerik yatırım tavsiyesi değildir. Veriler gecikmeli olabilir. © {datetime.now().year} Altın Saat")
