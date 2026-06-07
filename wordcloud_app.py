"""
Google Forms ワードクラウド アプリ（CSVアップロード方式）

使い方:
  streamlit run wordcloud_app.py

手順:
  1. Google Forms のスプレッドシートを開く
  2. ファイル → ダウンロード → CSV でダウンロード
  3. このアプリにCSVをアップロード → ワードクラウド生成
"""

import re
import io
import time
from collections import Counter

import pandas as pd
import streamlit as st
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# ─── 設定 ───────────────────────────────────────────────────────────────────
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
    "C:/Windows/Fonts/msgothic.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
]
STOP_POS = {"助詞", "助動詞", "記号", "接続詞", "感動詞", "接頭詞", "接頭辞"}
STOP_WORDS = {
    "する", "ある", "いる", "なる", "れる", "られる", "です", "ます", "ない",
    "こと", "もの", "ため", "よう", "それ", "これ", "あれ", "どれ",
    "の", "が", "を", "に", "は", "も", "で", "と", "や", "から",
    "について", "ほう", "ほど", "だ", "た", "て",
}

# ─── ユーティリティ ──────────────────────────────────────────────────────────

@st.cache_resource
def get_tokenizer():
    return Tokenizer()


def find_font():
    import os
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def load_csv(file) -> pd.DataFrame:
    content = file.read()
    for enc in ("utf-8-sig", "utf-8", "shift-jis", "cp932"):
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


# ─── Streamlit UI ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Google Forms ワードクラウド",
    page_icon="☁️",
    layout="wide",
)

st.title("☁️ Google Forms ワードクラウド")

# ─ サイドバー ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 設定")

    uploaded_file = st.file_uploader(
        "CSVファイルをアップロード",
        type=["csv"],
        help="Google Formsのスプレッドシートを「ファイル→ダウンロード→CSV」で保存したファイルを選択してください。",
    )

    st.divider()
    st.markdown("""
**📋 CSVの取得手順**

1. Google Forms の回答が保存された
   **スプレッドシート**を開く
2. 上メニュー「**ファイル**」をクリック
3. 「**ダウンロード**」→「**カンマ区切り形式（.csv）**」
4. ダウンロードされたCSVを
   上の枠にドラッグ＆ドロップ
""")

# ─ メイン ─────────────────────────────────────────────────────────────────────
if uploaded_file is None:
    st.info("← 左のサイドバーからCSVファイルをアップロードしてください。")

    st.subheader("📋 CSVファイルの取得方法")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**① Formsのスプレッドシートを開く**")
        st.markdown("Google Forms → 「回答」タブ → 🟩 スプレッドシートアイコン")
    with col2:
        st.markdown("**② CSVでダウンロード**")
        st.markdown("ファイル → ダウンロード → カンマ区切り形式（.csv）")
    with col3:
        st.markdown("**③ アップロード**")
        st.markdown("左のサイドバーの枠にCSVをドラッグ＆ドロップ")
    st.stop()

# ─ CSV読み込み ────────────────────────────────────────────────────────────────
try:
    df = load_csv(uploaded_file)
except Exception as e:
    st.error(f"CSVの読み込みに失敗しました: {e}")
    st.stop()

st.success(f"✅ {uploaded_file.name} を読み込みました（{len(df)} 件の回答）")

# ─ 列選択 ─────────────────────────────────────────────────────────────────────
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
        help="ワードクラウドに使う列を選択してください。自由記述の列を選ぶと効果的です。",
    )

if not selected_columns:
    st.warning("← 左のサイドバーで対象列を1つ以上選択してください。")
    st.stop()

# ─ ワードクラウド生成 ──────────────────────────────────────────────────────────
texts = []
for col in selected_columns:
    texts.extend(df[col].dropna().astype(str).tolist())

with st.spinner("ワードクラウドを生成中..."):
    words = tokenize(texts)

if not words:
    st.warning("有効な単語が抽出できませんでした。自由記述の列が選択されているか確認してください。")
    st.stop()

freq = Counter(words)

main_col, stat_col = st.columns([3, 1])

with main_col:
    fig = build_wordcloud(freq)
    st.pyplot(fig)
    plt.close(fig)

    # PNG保存ボタン
    buf = io.BytesIO()
    fig2 = build_wordcloud(freq)
    fig2.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig2)
    buf.seek(0)
    st.download_button(
        label="📥 ワードクラウドをPNGで保存",
        data=buf,
        file_name="wordcloud.png",
        mime="image/png",
    )

with stat_col:
    st.subheader("📊 統計")
    st.metric("回答数", len(df))
    st.metric("ユニーク単語数", len(freq))

    st.subheader("🏆 上位ワード")
    top_df = pd.DataFrame(freq.most_common(15), columns=["単語", "出現回数"])
    st.dataframe(top_df, hide_index=True, use_container_width=True)

st.caption(f"生成日時: {time.strftime('%Y-%m-%d %H:%M:%S')}")
