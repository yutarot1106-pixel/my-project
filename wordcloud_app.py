"""
Google Forms リアルタイム ワードクラウド アプリ

使い方:
  streamlit run wordcloud_app.py

準備:
  1. Google Forms で回答をスプレッドシートにリンク
  2. スプレッドシートを「リンクを知っている全員が閲覧可」に設定
  3. このアプリにスプレッドシートのURLを貼り付ける
"""

import re
import io
import time
import urllib.request
from collections import Counter

import pandas as pd
import streamlit as st
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# ─── 設定 ───────────────────────────────────────────────
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
]
STOP_POS = {"助詞", "助動詞", "記号", "接続詞", "感動詞", "接頭詞", "接頭辞"}
STOP_WORDS = {
    "する", "ある", "いる", "なる", "れる", "られる", "です", "ます", "ない",
    "こと", "もの", "ため", "よう", "それ", "これ", "あれ", "どれ",
    "の", "が", "を", "に", "は", "も", "で", "と", "や", "から",
    "について", "ほう", "ほど", "だ", "た", "て",
}

# ─── ユーティリティ ──────────────────────────────────────

@st.cache_resource
def get_tokenizer():
    return Tokenizer()


@st.cache_data(ttl=0)
def find_font():
    import os
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def sheet_url_to_csv_url(url: str) -> str | None:
    """スプレッドシートURLをCSVエクスポートURLに変換（pub形式を優先）"""
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not m:
        return None
    sheet_id = m.group(1)
    gid_m = re.search(r"[#&?]gid=(\d+)", url)
    gid = gid_m.group(1) if gid_m else "0"
    # ウェブ公開形式（"ウェブに公開"済みのシートで動作）
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/pub?output=csv&gid={gid}"


def fetch_csv(csv_url: str) -> pd.DataFrame:
    req = urllib.request.Request(
        csv_url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/csv,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read()
    # UTF-8 / Shift-JIS どちらでも対応
    for enc in ("utf-8-sig", "utf-8", "shift-jis"):
        try:
            return pd.read_csv(io.BytesIO(content), encoding=enc)
        except Exception:
            continue
    raise ValueError("CSVの文字コードを判別できませんでした。")


def tokenize(texts: list[str]) -> list[str]:
    tokenizer = get_tokenizer()
    words = []
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            continue
        for token in tokenizer.tokenize(text):
            surface = token.surface
            pos = token.part_of_speech.split(",")[0]
            parts = token.part_of_speech.split(",")
            base = parts[6] if len(parts) > 6 and parts[6] != "*" else surface
            if pos in STOP_POS:
                continue
            if len(surface) < 2:
                continue
            if surface in STOP_WORDS or base in STOP_WORDS:
                continue
            if re.match(r'^[0-9０-９]+$', surface):
                continue
            words.append(base)
    return words


def build_wordcloud(freq: dict) -> plt.Figure:
    font_path = find_font()
    wc = WordCloud(
        font_path=font_path,
        width=1400,
        height=800,
        background_color="white",
        max_words=150,
        max_font_size=140,
        min_font_size=10,
        colormap="tab10",
        collocations=False,
    ).generate_from_frequencies(freq)

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    plt.tight_layout(pad=0)
    return fig

# ─── Streamlit UI ────────────────────────────────────────

st.set_page_config(
    page_title="Google Forms ワードクラウド",
    page_icon="☁️",
    layout="wide",
)

st.title("☁️ Google Forms リアルタイム ワードクラウド")

# ─ サイドバー：設定 ──────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 設定")
    sheet_url = st.text_area(
        "スプレッドシート URL",
        placeholder="https://docs.google.com/spreadsheets/d/xxxxx/edit",
        height=100,
        help="Google Formsの回答が保存されているスプレッドシートのURLを貼り付けてください。",
    )
    refresh_interval = st.slider("自動更新間隔（秒）", 10, 300, 30, step=10)
    auto_refresh = st.toggle("自動更新", value=True)

    st.divider()
    st.markdown("""
**📋 準備手順**

1. Google Forms を開く
2. 「回答」タブ → スプレッドシートアイコンをクリック
3. スプレッドシートが開いたら「共有」→ **「リンクを知っている全員が閲覧可」** に設定
4. URLをコピーして上に貼り付ける
""")

# ─ メイン ────────────────────────────────────────────────
if not sheet_url.strip():
    st.info("← 左のサイドバーにスプレッドシートのURLを入力してください。")
    st.stop()

csv_url = sheet_url_to_csv_url(sheet_url.strip())
if not csv_url:
    st.error("スプレッドシートのURLが正しくありません。`/spreadsheets/d/` を含むURLを入力してください。")
    st.stop()

# ─ データ取得 ─────────────────────────────────────────────
status_placeholder = st.empty()
last_updated_placeholder = st.empty()

try:
    with st.spinner("データを取得中..."):
        df = fetch_csv(csv_url)
except Exception as e:
    st.error(f"データ取得に失敗しました: {e}\n\nスプレッドシートが公開設定になっているか確認してください。")
    st.stop()

# ─ 列選択 ────────────────────────────────────────────────
text_columns = [c for c in df.columns if df[c].dtype == object]
if not text_columns:
    st.warning("テキスト列が見つかりません。")
    st.stop()

with st.sidebar:
    st.divider()
    selected_columns = st.multiselect(
        "対象列（複数選択可）",
        options=text_columns,
        default=text_columns[1:] if len(text_columns) > 1 else text_columns,
        help="ワードクラウドに使う回答列を選択してください。",
    )

if not selected_columns:
    st.warning("対象列を少なくとも1つ選択してください。")
    st.stop()

# ─ ワードクラウド生成 ─────────────────────────────────────
texts = []
for col in selected_columns:
    texts.extend(df[col].dropna().astype(str).tolist())

words = tokenize(texts)

if not words:
    st.warning("有効な単語が抽出できませんでした。回答がまだない可能性があります。")
    st.stop()

freq = Counter(words)

col1, col2 = st.columns([3, 1])

with col1:
    fig = build_wordcloud(freq)
    st.pyplot(fig)
    plt.close(fig)

with col2:
    st.subheader("📊 統計")
    st.metric("回答数", len(df))
    st.metric("ユニーク単語数", len(freq))

    st.subheader("🏆 上位ワード")
    top_df = pd.DataFrame(freq.most_common(15), columns=["単語", "出現回数"])
    st.dataframe(top_df, hide_index=True, use_container_width=True)

last_updated_placeholder.caption(f"最終更新: {time.strftime('%H:%M:%S')}")

# ─ 自動更新 ───────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
