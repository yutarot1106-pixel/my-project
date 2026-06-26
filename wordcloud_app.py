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
from copy import deepcopy

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

# ─── フォント候補 ────────────────────────────────────────
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msgothic.ttc",
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothR.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
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

DEFAULT_CHANNEL = {
    "name": "チャネル 1",
    "urls": ["https://docs.google.com/spreadsheets/d/1PIFEKv7ylfnfeIyCgqipTFgijwYPzRctfjjHk4179bA/edit"],
    "min_count": 2,
}

# ─── ユーティリティ ─────────────────────────────────────

@st.cache_resource
def get_tokenizer():
    return Tokenizer()


def find_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def get_gspread_client():
    import gspread
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError

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
            try:
                creds.refresh(Request())
            except RefreshError:
                token_path.unlink(missing_ok=True)
                creds = None

        if not creds or not creds.valid:
            if not creds_path.exists():
                return None, "credentials.json が見つかりません。"
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return gspread.authorize(creds), None


def get_worksheet_titles(sheet_url: str):
    client, err = get_gspread_client()
    if err:
        return None, err
    try:
        sh = client.open_by_url(sheet_url)
        return [ws.title for ws in sh.worksheets()], None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


@st.cache_data(ttl=60, show_spinner=False)
def cached_get_titles(sheet_url: str):
    return get_worksheet_titles(sheet_url)


@st.cache_data(ttl=30, show_spinner=False)
def cached_fetch_all(sheet_url: str, sheet_titles_key: str):
    import gspread
    import time as _time
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
                _time.sleep(2 ** attempt)
                continue
            return None, None, "APIエラー（レート制限）: しばらく待ってから再試行してください。"
        except Exception as e:
            return None, None, f"{type(e).__name__}: {e}"


def clean_text(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    text = re.sub(r"\b[A-Za-z0-9]{6,}\b", "", text)
    text = re.sub(r"[^\w\sぁ-んァ-ン一-龥ーａ-ｚＡ-Ｚ０-９]", " ", text)
    return text


def is_noise(surface: str, base: str) -> bool:
    if re.match(r"^[a-zA-Z]{1,3}$", surface):
        return True
    if re.match(r"^(?=.*[A-Z])(?=.*[a-z])[A-Za-z0-9]{5,}$", surface):
        return True
    if surface in ("http", "https", "www", "com", "jp", "gle"):
        return True
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


def build_wordcloud(freq: dict, title: str) -> plt.Figure:
    import numpy as np
    font = find_font()
    W, H = 1400, 800

    # タイトル用に左上の領域を確保するマスクを作成
    # （白=255の領域には単語が描画されない）
    mask = None
    title_w_frac, title_h_frac = 0.0, 0.0
    if title:
        # タイトル文字数に応じて確保する幅を調整
        title_w_frac = min(0.15 + len(title) * 0.038, 0.55)
        title_h_frac = 0.13
        mask = np.zeros((H, W), dtype=np.uint8)
        mask[: int(H * title_h_frac), : int(W * title_w_frac)] = 255

    wc = WordCloud(
        font_path=font,
        width=W, height=H,
        background_color="white",
        max_words=150,
        max_font_size=160, min_font_size=12,
        colormap="tab10",
        collocations=False,
        mask=mask,
    ).generate_from_frequencies(freq)

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")

    # 確保した左上領域にタイトルを描画（日本語フォントを明示指定）
    if title:
        from matplotlib import font_manager
        title_font = font_manager.FontProperties(fname=font, size=40)
        title_font.set_weight("bold")
        ax.text(
            0.02, 0.95, title,
            transform=ax.transAxes,
            fontproperties=title_font,
            verticalalignment="top", horizontalalignment="left",
            color="#222222",
            bbox=dict(
                facecolor="white", alpha=0.95,
                edgecolor="#333333", linewidth=2.5,
                boxstyle="round,pad=0.5,rounding_size=0.4",
            ),
        )

    plt.tight_layout(pad=0)
    return fig


def fetch_channel_data(channel: dict):
    """チャネル設定からテキスト・ヘッダー・データを取得"""
    urls = [u.strip() for u in channel.get("urls", []) if u.strip()]
    all_headers = None
    all_data = []

    for url in urls:
        titles, err = cached_get_titles(url)
        if err or not titles:
            continue
        titles_key = "|||".join(titles)
        headers, data, err = cached_fetch_all(url, titles_key)
        if err or headers is None:
            continue
        if all_headers is None:
            all_headers = headers
        all_data.extend(data)

    return all_headers, all_data


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

# ─── セッションステート初期化 ────────────────────────────
if "channels" not in st.session_state:
    st.session_state.channels = [deepcopy(DEFAULT_CHANNEL)]

# ─── サイドバー ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 設定")

    # ── グローバル設定 ──
    rotation_interval = st.slider("チャネル切替間隔（秒）", 5, 300, 30, step=5)
    auto_rotate = st.toggle("自動切替", value=True)
    data_refresh = st.slider("データ更新間隔（秒）", 5, 300, 60, step=5)
    min_count = st.slider("最低出現回数", 1, 10, 2, step=1)

    st.divider()

    # ── チャネル管理 ──
    st.markdown("**📺 チャネル設定**")
    ch_to_delete = None

    for i, ch in enumerate(st.session_state.channels):
        with st.expander(f"チャネル {i+1}：{ch['name']}", expanded=(i == 0)):
            ch["name"] = st.text_input(
                "タイトル", value=ch["name"], key=f"ch_name_{i}"
            )

            # URL管理
            st.caption("スプレッドシート URL")
            url_to_delete = None
            for j, url in enumerate(ch["urls"]):
                c1, c2 = st.columns([10, 1])
                with c1:
                    ch["urls"][j] = st.text_input(
                        f"URL {j+1}", value=url,
                        key=f"ch_{i}_url_{j}",
                        label_visibility="collapsed",
                    )
                with c2:
                    if len(ch["urls"]) > 1 and st.button("✕", key=f"ch_{i}_del_url_{j}"):
                        url_to_delete = j

            if url_to_delete is not None:
                ch["urls"].pop(url_to_delete)
                st.rerun()

            if st.button("＋ URL追加", key=f"ch_{i}_add_url"):
                ch["urls"].append("")
                st.rerun()

            if len(st.session_state.channels) > 1:
                if st.button(f"🗑 チャネル {i+1} を削除", key=f"del_ch_{i}"):
                    ch_to_delete = i

    if ch_to_delete is not None:
        st.session_state.channels.pop(ch_to_delete)
        st.rerun()

    if st.button("＋ チャネルを追加"):
        n = len(st.session_state.channels) + 1
        st.session_state.channels.append({
            "name": f"チャネル {n}",
            "urls": [""],
            "min_count": 2,
        })
        st.rerun()

# ─── 自動更新・チャネル切替 ──────────────────────────────
num_channels = len(st.session_state.channels)

# データ更新タイマーは常に動かす
st_autorefresh(interval=data_refresh * 1000, key="data_refresh")

if auto_rotate and num_channels > 1:
    # チャネル切替タイマー（rotation_interval秒ごとにカウントアップ）
    rotate_count = st_autorefresh(interval=rotation_interval * 1000, key="rotate")
    current_idx = rotate_count % num_channels
else:
    current_idx = 0

channel = st.session_state.channels[current_idx]

# ─── チャネルインジケーター ──────────────────────────────
if num_channels > 1:
    dots = "  ".join(
        f"🔵" if i == current_idx else "⚪"
        for i in range(num_channels)
    )
    st.caption(f"チャネル {current_idx + 1} / {num_channels}　　{dots}")

# ─── データ取得 ──────────────────────────────────────────
with st.spinner(f"「{channel['name']}」のデータを取得中..."):
    headers, data = fetch_channel_data(channel)

if not headers or not data:
    st.warning(f"「{channel['name']}」のデータが取得できませんでした。URLとスプレッドシートの設定を確認してください。")
    st.stop()

# ─── テキスト収集 ────────────────────────────────────────
col_options = [h for h in headers if "タイムスタンプ" not in h and h]
texts = []
for row in data:
    for h in col_options:
        if h in headers:
            i = headers.index(h)
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
freq = Counter({w: c for w, c in freq.items() if c >= min_count})

if not freq:
    st.warning(f"{min_count}回以上登場する単語がありません。「最低出現回数」を下げてみてください。")
    st.stop()

col1, col2 = st.columns([3, 1])

with col1:
    fig = build_wordcloud(freq, channel["name"])

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # フェードイン効果（st.image を使うことで最大化ボタンも維持）
    # 更新のたびにアニメーション名を変えて、同じ<img>要素でも強制的に再生させる
    # （通常表示・フルスクリーン表示の両方で再生される）
    st.session_state["render_tick"] = st.session_state.get("render_tick", 0) + 1
    tick = st.session_state["render_tick"]
    st.markdown(
        f"""
        <style>
        @keyframes wcFade{tick} {{
            from {{ opacity: 0; transform: scale(0.985); }}
            to   {{ opacity: 1; transform: scale(1); }}
        }}
        [data-testid="stImage"] img,
        [data-testid="stImageContainer"] img,
        [data-testid="stFullScreenFrame"] img,
        [data-testid="stExpandedFullScreenFrame"] img {{
            animation: wcFade{tick} 1s ease-out;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.image(buf.getvalue(), use_container_width=True)

    st.download_button(
        "📥 PNGで保存",
        data=buf.getvalue(),
        file_name=f"wordcloud_{time.strftime('%Y%m%d_%H%M%S')}.png",
        mime="image/png",
    )

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

# ─── 選択単語の回答表示 ──────────────────────────────────
if not selected_word:
    st.stop()

st.divider()
st.subheader(f"💬「{selected_word}」を含む回答")

col_indices = [headers.index(h) for h in col_options if h in headers]

def extract_sentences(text: str, word: str) -> list[str]:
    sentences = re.split(r"[。！？\n]+", text)
    matched = [s.strip() for s in sentences if word in s and s.strip()]
    return matched if matched else [text.strip()]

matched_rows = []
for row in data:
    for i in col_indices:
        if i < len(row):
            cell = row[i]
            if selected_word in cell:
                for sent in extract_sentences(cell, selected_word):
                    highlighted = sent.replace(
                        selected_word, f"**:red[{selected_word}]**"
                    )
                    matched_rows.append(highlighted)

if matched_rows:
    for i, text in enumerate(matched_rows, 1):
        st.markdown(f"{i}. {text}")
else:
    st.info("該当する回答が見つかりませんでした。")
