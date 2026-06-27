"""
Google Forms回答からワードクラウドを生成するスクリプト

使い方:
  python generate_wordcloud.py [CSVファイル] [対象列名またはインデックス]

例:
  python generate_wordcloud.py responses.csv "回答"
  python generate_wordcloud.py responses.csv 2
  python generate_wordcloud.py  # サンプルデータで実行

"""

import sys
import os
import re
import pandas as pd
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter

# 日本語フォントパス（優先順）
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]

# ワードクラウドに含めない品詞・語
STOP_POS = {"助詞", "助動詞", "記号", "接続詞", "感動詞", "接頭詞", "接頭辞"}
STOP_WORDS = {
    "する", "ある", "いる", "なる", "れる", "られる", "です", "ます", "ない",
    "こと", "もの", "ため", "よう", "それ", "これ", "あれ", "どれ",
    "の", "が", "を", "に", "は", "も", "で", "と", "や", "から",
    "について", "に関して", "ほう", "ほど", "だ", "た", "て", "に",
}

# サンプルデータ（CSVが未指定の場合に使用）
SAMPLE_RESPONSES = [
    "この製品はとても使いやすく、デザインも素晴らしいと思います。",
    "サポートの対応が迅速で非常に助かりました。問題が早く解決できてよかったです。",
    "価格が少し高いと感じますが、品質は申し分ないです。",
    "UIがシンプルで初心者にも使いやすいです。機能も充実しています。",
    "配送が遅かったのが残念でした。商品自体は満足しています。",
    "とても便利なサービスです。毎日活用しています。",
    "機能が豊富で、仕事の効率が大幅に向上しました。",
    "操作が直感的でわかりやすい。デザインもシンプルで好きです。",
    "サポートチームの対応が丁寧で信頼できます。",
    "コスパが良く、非常に満足しています。また購入したいと思います。",
    "インターフェースが使いやすく、業務の効率化に役立っています。",
    "品質が高く、耐久性もあるので長く使えそうです。",
    "初回の設定が少し複雑でしたが、慣れると非常に便利です。",
    "デザインがおしゃれで、使っていて気分が上がります。",
    "機能が多すぎて最初は戸惑いましたが、徐々に慣れてきました。",
]


def find_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("日本語フォントが見つかりません。IPAフォントをインストールしてください。")


def tokenize_japanese(texts: list[str]) -> list[str]:
    tokenizer = Tokenizer()
    words = []
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            continue
        for token in tokenizer.tokenize(text):
            surface = token.surface
            pos = token.part_of_speech.split(",")[0]
            base = token.part_of_speech.split(",")[6] if len(token.part_of_speech.split(",")) > 6 else surface

            # フィルタリング
            if pos in STOP_POS:
                continue
            if len(surface) < 2:
                continue
            if surface in STOP_WORDS or base in STOP_WORDS:
                continue
            if re.match(r'^[0-9０-９]+$', surface):
                continue

            words.append(base if base != "*" else surface)
    return words


def load_csv(filepath: str, column) -> list[str]:
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    print(f"読み込み: {filepath} ({len(df)}行, {len(df.columns)}列)")
    print(f"列名: {list(df.columns)}")

    if isinstance(column, int):
        col = df.iloc[:, column]
    else:
        if column in df.columns:
            col = df[column]
        else:
            # 部分一致で列を探す
            matches = [c for c in df.columns if column in c]
            if not matches:
                raise ValueError(f"列 '{column}' が見つかりません。利用可能な列: {list(df.columns)}")
            col = df[matches[0]]
            print(f"列 '{matches[0]}' を使用します。")

    return col.dropna().astype(str).tolist()


def generate_wordcloud(texts: list[str], output_path: str = "wordcloud_output.png"):
    print(f"テキスト数: {len(texts)}")
    words = tokenize_japanese(texts)

    if not words:
        print("有効な単語が見つかりませんでした。")
        return

    freq = Counter(words)
    print(f"ユニーク単語数: {len(freq)}")
    print("上位20語:", freq.most_common(20))

    font_path = find_font()
    print(f"使用フォント: {font_path}")

    wc = WordCloud(
        font_path=font_path,
        width=1200,
        height=800,
        background_color="white",
        max_words=150,
        max_font_size=120,
        min_font_size=10,
        colormap="tab10",
        collocations=False,
    ).generate_from_frequencies(freq)

    plt.figure(figsize=(15, 10))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"保存完了: {output_path}")


def main():
    if len(sys.argv) >= 2:
        csv_path = sys.argv[1]
        column = sys.argv[2] if len(sys.argv) >= 3 else 1
        # 数値なら整数に変換
        try:
            column = int(column)
        except ValueError:
            pass
        texts = load_csv(csv_path, column)
        output = os.path.splitext(csv_path)[0] + "_wordcloud.png"
    else:
        print("CSVファイルが指定されていないため、サンプルデータで実行します。")
        texts = SAMPLE_RESPONSES
        output = "wordcloud_output.png"

    generate_wordcloud(texts, output)


if __name__ == "__main__":
    main()
