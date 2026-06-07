"""
Google Forms リアルタイム ワードクラウド アプリ

使い方:
  python -m streamlit run wordcloud_app.py

初回起動時にブラウザでGoogleログインが求められます。
以降は自動でスプレッドシートからデータを取得します。
"""

import re
import os
import io
import time
from collections import Counter
from pathlib import Path

import streamlit as st
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# ─── 設定 ────────────────────────────────────────────────
FONT_CANDIDATES = [
    # Windows
    r"C:\Windows\Fonts\msgothic.ttc",
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothR.ttc",
    # Mac
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/Library/Fonts/Osaka.ttf",
    # Linux
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]
STOP_POS = {"助詞", "助動詞", "記号", "接続詞", "感動詞", "接頭詞", "接頭辞"}
STOP_WORDS = {
    "する", "ある", "いる", "なる", "れる", "られる", "です", "ます", "ない",
    "こと", "もの", "ため", "よう", "それ", "これ", "あれ", "どれ",
    "の", "が", "を", "に", "は", "も", "で", "と", "や", "から",
    "について", "ほう", "ほど", "だ", "た", "て", "今", "ここ",
}

# ─── ユーティリティ ─────────────────────────────────────

@st.cache_resource
def get_tokenizer():
    return Tokenizer()


def find_font() -> str | None:
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def get_gspread_client():
    """gspreadクライアントを返す。初回はブラウザでGoogle認証を行う。"""
    import gspread
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    token_path = Path("token.json")
    creds_path = Path("credentials.json")
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                return None, "credentials.json が見つかりません。"
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return gspread.authorize(creds), None


def fetch_sheet_data(sheet_url: str):
    client, err = get_gspread_client()
    if err:
        return None, None, err
    try:
        sh = client.open_by_url(sheet_url)
        ws = sh.get_worksheet(0)
        rows = ws.get_all_values()
        if not rows:
            return None, None, "シートにデータがありません。"
        headers = rows[0] if rows else []
        data = rows[1:] if len(rows) > 1 else []
        return headers, data, None
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"


def clean_text(text: str) -> str:
    """URLや記号などのノイズを除去してからトークナイズに渡す"""
    # URLを除去
    text = re.sub(r"https?://\S+", "", text)
    # メールアドレスを除去
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    # ランダムな英数字の羅列（6文字以上の大小混在英数字）を除去
    text = re.sub(r"\b[A-Za-z0-9]{6,}\b", "", text)
    # 記号・特殊文字を除去（日本語・英数字・スペース以外）
    text = re.sub(r"[^\w\sぁ-んァ-ン一-龥ーａ-ｚＡ-Ｚ０-９]", " ", text)
    return text


def is_noise(surface: str, base: str) -> bool:
    """ノイズ判定：除外すべき単語ならTrue"""
    # 英字のみで3文字以下
    if re.match(r"^[a-zA-Z]{1,3}$", surface):
        return True
    # ランダムな英数字混在（大文字・小文字・数字が混在する5文字以上）
    if re.match(r"^(?=.*[A-Z])(?=.*[a-z])[A-Za-z0-9]{5,}$", surface):
        return True
    # URLの残骸
    if surface in ("http", "https", "www", "com", "jp", "gle"):
        return True
    # 記号のみ
    if re.match(r"^[^\w]+$", surface):
        return True
    return False


def tokenize(texts: list[str]) -> list[str]:
    t = get_tokenizer()
    words = []
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            continue
        text = clean_text(text)
        for token in t.tokenize(text):
            surface = token.surface
            parts = token.part_of_speech.split(",")
            pos = parts[0]
            base = parts[6] if len(parts) > 6 and parts[6] != "*" else surface
            if pos in STOP_POS:
                continue
            if len(surface) < 2:
                continue
            if surface in STOP_WORDS or base in STOP_WORDS:
                continue
            if re.match(r"^[0-9０-９]+$", surface):
                continue
            if is_noise(surface, base):
                continue
            words.append(base)
    return words


def build_wordcloud(freq: dict) -> plt.Figure:
    font = find_font()
    wc = WordCloud(
        font_path=font,
        width=1400, height=800,
        background_color="white",
        max_words=150,
        max_font_size=160, min_font_size=12,
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

# ─── credentials.json がない場合はセットアップ案内 ─────
if not Path("credentials.json").exists():
    st.error("⚠️ **初回セットアップが必要です。** `credentials.json` が見つかりません。")
    with st.expander("📋 セットアップ手順（クリックして開く）", expanded=True):
        st.markdown("""
### 手順1：Google Cloud Console でプロジェクト作成
1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. 「プロジェクトを選択」→「新しいプロジェクト」→ 任意の名前で作成

### 手順2：APIを有効化
1. 左メニュー「APIとサービス」→「ライブラリ」
2. 「**Google Sheets API**」を検索 → 「有効にする」
3. 同様に「**Google Drive API**」も有効にする

### 手順3：OAuth認証情報を作成
1. 「APIとサービス」→「認証情報」→「認証情報を作成」→「**OAuthクライアントID**」
2. アプリケーションの種類：**デスクトップアプリ**
3. 名前を入力して「作成」
4. 「**JSONをダウンロード**」でファイルを保存
5. ダウンロードしたファイル名を **`credentials.json`** に変更
6. このアプリのフォルダ（`my-project`）に置く

### 手順4：アプリを再起動
```
python -m streamlit run wordcloud_app.py
```
ブラウザでGoogleログイン画面が開きます。許可すると自動で動き始めます。
""")
    st.stop()

# ─── サイドバー ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 設定")
    sheet_url = st.text_area(
        "スプレッドシート URL",
        value="https://docs.google.com/spreadsheets/d/1WkHCs-NsXj8Y2yuPdINwwQRhKH13ynjm5a5OoJLYRb8/edit",
        height=120,
    )
    refresh_interval = st.slider("自動更新間隔（秒）", 10, 300, 60, step=10)
    auto_refresh = st.toggle("自動更新", value=True)
    min_count = st.slider("最低出現回数", 1, 10, 2, step=1, help="この回数以上登場した単語だけ表示します")
    st.button("🔄 今すぐ更新")

if not sheet_url.strip():
    st.info("← スプレッドシートのURLを入力してください。")
    st.stop()

# ─── データ取得 ──────────────────────────────────────────
with st.spinner("スプレッドシートからデータを取得中..."):
    headers, data, err = fetch_sheet_data(sheet_url.strip())

if err or headers is None:
    st.error(f"データ取得エラー: {err or 'ヘッダーが取得できませんでした'}")
    st.stop()

# ─── 列選択 ─────────────────────────────────────────────
with st.sidebar:
    st.divider()
    col_options = [h for h in headers if "タイムスタンプ" not in h and h]
    selected_cols = st.multiselect(
        "対象列（複数選択可）",
        options=col_options,
        default=col_options,
    )

if not selected_cols:
    st.warning("対象列を選択してください。")
    st.stop()

col_indices = [headers.index(c) for c in selected_cols if c in headers]
texts = []
for row in data:
    for i in col_indices:
        if i < len(row) and row[i].strip():
            texts.append(row[i])

if not texts:
    st.warning("有効な回答がまだありません。")
    st.stop()

# ─── ワードクラウド生成 ──────────────────────────────────
words = tokenize(texts)
if not words:
    st.warning("単語を抽出できませんでした。")
    st.stop()

freq = Counter(words)
# 最低出現回数でフィルタ（Counterのまま保持）
freq = Counter({w: c for w, c in freq.items() if c >= min_count})

if not freq:
    st.warning(f"{min_count}回以上登場する単語がありません。左の「最低出現回数」を下げてみてください。")
    st.stop()

col1, col2 = st.columns([3, 1])

with col1:
    fig = build_wordcloud(freq)
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    st.download_button(
        "📥 PNGで保存",
        data=buf.getvalue(),
        file_name=f"wordcloud_{time.strftime('%Y%m%d_%H%M%S')}.png",
        mime="image/png",
    )
    plt.close(fig)

with col2:
    st.subheader("📊 統計")
    st.metric("回答数", len(data))
    st.metric("ユニーク単語数", len(freq))
    st.caption(f"最終更新: {time.strftime('%H:%M:%S')}")

    st.subheader("🏆 上位ワード")
    top_df = pd.DataFrame(freq.most_common(15), columns=["単語", "出現回数"])
    st.dataframe(top_df, hide_index=True, use_container_width=True)

# ─── 自動更新 ────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
