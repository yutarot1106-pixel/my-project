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
from streamlit_autorefresh import st_autorefresh
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


def get_worksheet_titles(sheet_url: str):
    """スプレッドシート内の全シート名を返す"""
    client, err = get_gspread_client()
    if err:
        return None, err
    try:
        sh = client.open_by_url(sheet_url)
        return [ws.title for ws in sh.worksheets()], None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


@st.cache_data(ttl=30, show_spinner=False)
def cached_fetch_all(sheet_url: str, sheet_titles_key: str):
    """全タブで共有するキャッシュ付きデータ取得（30秒TTL）。
    sheet_titles_key は tuple をそのまま渡すと unhashable なので str 化して渡す。
    """
    import gspread, time as _time
    sheet_titles = sheet_titles_key.split("|||")
    client, err = get_gspread_client()
    if err:
        return None, None, err
    for attempt in range(4):
        try:
            sh = client.open_by_url(sheet_url)
            headers = None
            all_data = []
            for title in sheet_titles:
                ws = sh.worksheet(title)
                rows = ws.get_all_values()
                if not rows:
                    continue
                if headers is None:
                    headers = rows[0]
                all_data.extend(rows[1:])
            if headers is None:
                return None, None, "選択したシートにデータがありません。"
            return headers, all_data, None
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429 and attempt < 3:
                _time.sleep(2 ** attempt)   # 1秒 → 2秒 → 4秒
                continue
            return None, None, f"APIエラー（レート制限）: しばらく待ってから再試行してください。"
        except Exception as e:
            return None, None, f"{type(e).__name__}: {e}"


@st.cache_data(ttl=60, show_spinner=False)
def cached_get_titles(sheet_url: str):
    """シート名一覧もキャッシュ（60秒TTL）"""
    return get_worksheet_titles(sheet_url)


def fetch_sheet_data(sheet_url: str, sheet_titles: list[str]):
    """指定した複数シートのデータを合算して返す"""
    client, err = get_gspread_client()
    if err:
        return None, None, err
    try:
        sh = client.open_by_url(sheet_url)
        headers = None
        all_data = []
        for title in sheet_titles:
            ws = sh.worksheet(title)
            rows = ws.get_all_values()
            if not rows:
                continue
            if headers is None:
                headers = rows[0]
            # ヘッダーが異なるシートは列数を合わせてスキップせず取り込む
            all_data.extend(rows[1:])
        if headers is None:
            return None, None, "選択したシートにデータがありません。"
        return headers, all_data, None
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
    app_title = st.text_input(
        "タイトル",
        value="Google Forms リアルタイム ワードクラウド",
        help="ページ上部に表示されるタイトルを自由に変更できます。",
    )

    st.divider()

    # ─ 複数スプレッドシートURL管理 ──────────────────────────
    if "sheet_urls" not in st.session_state:
        st.session_state.sheet_urls = [
            "https://docs.google.com/spreadsheets/d/1PIFEKv7ylfnfeIyCgqipTFgijwYPzRctfjjHk4179bA/edit"
        ]

    st.markdown("**📋 スプレッドシート URL**")
    urls_to_delete = []
    for i, url in enumerate(st.session_state.sheet_urls):
        col_url, col_del = st.columns([10, 1])
        with col_url:
            st.session_state.sheet_urls[i] = st.text_input(
                f"URL {i+1}",
                value=url,
                key=f"url_{i}",
                label_visibility="collapsed",
            )
        with col_del:
            if len(st.session_state.sheet_urls) > 1:
                if st.button("✕", key=f"del_{i}"):
                    urls_to_delete.append(i)

    for i in sorted(urls_to_delete, reverse=True):
        st.session_state.sheet_urls.pop(i)
        st.rerun()

    if st.button("＋ スプレッドシートを追加"):
        st.session_state.sheet_urls.append("")
        st.rerun()

    st.divider()
    refresh_interval = st.slider("自動更新間隔（秒）", 10, 300, 60, step=10)
    auto_refresh = st.toggle("自動更新", value=True)
    min_count = st.slider("最低出現回数", 1, 10, 2, step=1, help="この回数以上登場した単語だけ表示します")
    st.button("🔄 今すぐ更新")

st.title(f"☁️ {app_title}")

# 非ブロッキング自動更新（タブごとに独立して動作）
if auto_refresh:
    st_autorefresh(interval=refresh_interval * 1000, key="autorefresh")

active_urls = [u.strip() for u in st.session_state.sheet_urls if u.strip()]
if not active_urls:
    st.info("← 左のサイドバーにスプレッドシートのURLを入力してください。")
    st.stop()

# ─── 全スプレッドシートからシート一覧取得 ────────────────
all_sheet_options = {}   # {url: [sheet_title, ...]}
fetch_errors = []

with st.spinner("シート一覧を取得中..."):
    for url in active_urls:
        titles, err = cached_get_titles(url)
        if err or titles is None:
            fetch_errors.append(f"`{url[:60]}...` → {err}")
        else:
            all_sheet_options[url] = titles

if fetch_errors:
    for e in fetch_errors:
        st.error(f"シート取得エラー: {e}")

if not all_sheet_options:
    st.stop()

# ─── シート選択（スプレッドシートごと） ─────────────────
selected_sheets_per_url = {}
with st.sidebar:
    st.divider()
    for url, titles in all_sheet_options.items():
        short = url.split("/d/")[1][:12] + "..." if "/d/" in url else url[:20]
        selected = st.multiselect(
            f"シート（{short}）",
            options=titles,
            default=titles,
            key=f"sheets_{url}",
        )
        if selected:
            selected_sheets_per_url[url] = selected

if not selected_sheets_per_url:
    st.warning("対象シートを選択してください。")
    st.stop()

# ─── 全スプレッドシートのデータを取得・合算 ─────────────
all_headers = None
all_data = []

with st.spinner(f"データを取得中（{len(selected_sheets_per_url)}スプレッドシート）..."):
    for url, sheets in selected_sheets_per_url.items():
        titles_key = "|||".join(sheets)
        headers, data, err = cached_fetch_all(url, titles_key)
        if err or headers is None:
            st.warning(f"取得スキップ: {url[:50]}... → {err}")
            continue
        if all_headers is None:
            all_headers = headers
        all_data.extend(data)

if all_headers is None or not all_data:
    st.error("有効なデータが取得できませんでした。")
    st.stop()

headers = all_headers
data    = all_data

# ─── 列選択 ─────────────────────────────────────────────
with st.sidebar:
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
    top_words = [w for w, _ in freq.most_common(15)]
    top_counts = {w: c for w, c in freq.most_common(15)}

    selected_word = st.pills(
        "単語をクリックすると回答を表示",
        options=top_words,
        format_func=lambda w: f"{w}（{top_counts[w]}）",
        selection_mode="single",
        default=None,
    )

# 選択が外れたら表示をリセット
if not selected_word:
    st.stop()

# ─── 選択単語の回答表示 ───────────────────────────────────
if selected_word:
    st.divider()
    st.subheader(f"💬「{selected_word}」を含む回答")

    def extract_sentences(text: str, word: str) -> list[str]:
        """テキストから単語を含む文だけ抜き出す"""
        # 句点・感嘆符・改行で文を分割
        sentences = re.split(r"[。！？\n]+", text)
        matched = [s.strip() for s in sentences if word in s and s.strip()]
        return matched if matched else [text.strip()]

    matched_rows = []
    for row in data:
        for i in col_indices:
            if i < len(row):
                cell = row[i]
                if selected_word in cell:
                    sentences = extract_sentences(cell, selected_word)
                    for sent in sentences:
                        # 選択単語をハイライト表示
                        highlighted = sent.replace(
                            selected_word,
                            f"**:red[{selected_word}]**"
                        )
                        matched_rows.append(highlighted)

    if matched_rows:
        for i, text in enumerate(matched_rows, 1):
            st.markdown(f"{i}. {text}")
    else:
        st.info("該当する回答が見つかりませんでした。")

