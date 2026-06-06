#!/usr/bin/env python3
"""Generate Flash LiDAR research report PDF."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os

OUTPUT_PATH = "/home/user/my-project/flash_lidar_survey.pdf"

# ---- Register Japanese-capable font if available, else fall back ----
FONT_NAME = "Helvetica"
try:
    # Try to use a system CJK font for Japanese
    cjk_candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
        "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
    ]
    for path in cjk_candidates:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("CJK", path))
            FONT_NAME = "CJK"
            break
except Exception:
    pass

def style(name, **kwargs):
    base = getSampleStyleSheet()[name]
    kw = {"fontName": FONT_NAME}
    kw.update(kwargs)
    s = ParagraphStyle(
        name + "_custom",
        parent=base,
        **kw
    )
    return s

H1 = style("Heading1", fontSize=18, textColor=colors.HexColor("#1a3a5c"), spaceAfter=6)
H2 = style("Heading2", fontSize=13, textColor=colors.HexColor("#1a3a5c"), spaceAfter=4, spaceBefore=10)
H3 = style("Heading3", fontSize=11, textColor=colors.HexColor("#2c5f8a"), spaceAfter=3, spaceBefore=6)
BODY = style("Normal", fontSize=9, leading=14, spaceAfter=4)
CAPTION = style("Normal", fontSize=8, textColor=colors.gray, leading=11)
BULLET = style("Normal", fontSize=9, leading=14, leftIndent=12, spaceAfter=3)

def para(text, st=None):
    return Paragraph(text, st or BODY)

def bullet(text):
    return Paragraph(f"&#8226; {text}", BULLET)

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa"), spaceAfter=4)

# ---- Document content ----
content = []

# Title
content.append(Spacer(1, 10*mm))
content.append(para("<b>Flash LiDAR 技術調査レポート</b><br/>構造・構成に関する基礎解説論文サーベイ", H1))
content.append(para("調査日：2026年6月6日　|　対象：学術論文・技術レビュー", CAPTION))
content.append(hr())
content.append(Spacer(1, 4*mm))

# ============================================================
# 1. Flash LiDAR の基本動作原理
# ============================================================
content.append(para("1. Flash LiDAR の基本動作原理", H2))
content.append(para(
    "Flash LiDAR（フラッシュ型 LiDAR）は、単一の広域レーザーパルス（フラッド照明）で"
    "シーン全体を一括照射し、2次元フォトディテクタアレイで反射光を同時計測する非走査型"
    "距離計測システムである。各画素が独立に飛行時間（Time-of-Flight: ToF）を計測し、"
    "一フレームで3次元点群を取得できる点が最大の特徴である。"
))
content.append(para(
    "距離計算の基本式は <b>d = c &middot; &Delta;t / 2</b>（c：光速、&Delta;t：往復飛行時間）であり、"
    "ナノ秒〜ピコ秒オーダーのタイミング精度が要求される。"
    "レーザー光源には主に近赤外域（905 nm または 1550 nm）のパルスレーザーが使用される。"
))

# ============================================================
# 2. センサー構造と構成要素
# ============================================================
content.append(para("2. センサー構造と主要構成要素", H2))

content.append(para("2.1 送光部（Transmitter）", H3))
content.append(bullet("光源：パルスレーザーダイオード（LD）または VCSEL（垂直共振器面発光レーザー）アレイ"))
content.append(bullet("照射方式：ビームエキスパンダーやディフューザーで広角フラッド照明に変換"))
content.append(bullet("波長：905 nm（Si 受光素子向け）または 1550 nm（InGaAs 受光素子向け・アイセーフ）"))
content.append(bullet("パルス幅：数 ns〜数十 ns のショートパルス（高距離分解能のため）"))

content.append(para("2.2 受光部（Receiver / Detector Array）", H3))
content.append(bullet(
    "<b>Geiger-mode APD（GM-APD）/ SPAD（Single-Photon Avalanche Diode）アレイ</b>："
    "単一光子感度を持ち、ピコ秒レベルのタイミング精度を実現。"
    "CMOS プロセスと親和性が高く、高集積化が可能。"
    "各画素に TDC（Time-to-Digital Converter）またはアナログカウンタを内蔵。"
))
content.append(bullet(
    "<b>線形モード APD（LM-APD）アレイ</b>："
    "ゲインは GM-APD より低いが、線形応答でダイナミックレンジが広い。"
    "InGaAs ベースで 1550 nm 帯に対応。光ファイバー結合型も存在。"
))
content.append(bullet(
    "<b>SiPM（Silicon Photomultiplier）アレイ</b>："
    "多数の SPAD を並列接続したアナログ出力素子。"
    "高感度・高ダイナミックレンジだが画素ピッチが大きい。"
))

content.append(para("2.3 信号処理部（Signal Processing）", H3))
content.append(bullet("TDC（Time-to-Digital Converter）：光子到達時刻をデジタル値に変換"))
content.append(bullet("ヒストグラム処理：複数パルスの ToF 統計を蓄積し、SBR（Signal-to-Background Ratio）を改善"))
content.append(bullet("オンチップ処理：最新設計では読み出し遅延 2.4 &mu;s 以下の非同期処理を実現"))
content.append(bullet("後処理：点群生成、デノイジング、深度補完アルゴリズム"))

content.append(para("2.4 光学系", H3))
content.append(bullet("受光側：集光レンズ + 狭帯域 NIR バンドパスフィルター（太陽光背景雑音除去）"))
content.append(bullet("送光側：ビーム整形光学系（均一フラッド照明の実現）"))

# ============================================================
# 3. ToF との関係
# ============================================================
content.append(para("3. ToF（Time-of-Flight）との関係", H2))
content.append(para(
    "Flash LiDAR は dToF（Direct Time-of-Flight）方式の代表実装である。"
    "ToF 深度センサーの分類を以下に整理する。"
))

tof_data = [
    ["方式", "測定原理", "代表実装", "特徴"],
    ["dToF\n（直接 ToF）", "パルス往復時間を直接計時", "Flash LiDAR\n（SPAD アレイ）", "長距離・高精度\nSBR 問題あり"],
    ["iToF\n（間接 ToF）", "変調光の位相差から距離算出", "RGB-D カメラ\n（Intel RealSense 等）", "短距離・低コスト\n折り返し誤差あり"],
    ["FMCW LiDAR", "周波数掃引連続波の干渉計測", "コヒーレント LiDAR", "速度同時計測可\nシステム複雑"],
]
tof_table = Table(tof_data, colWidths=[28*mm, 45*mm, 45*mm, 50*mm])
tof_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
    ("GRID", (0, 0), (-1, -1), 0.3, colors.gray),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
content.append(tof_table)
content.append(Spacer(1, 4*mm))

# ============================================================
# 4. Flash LiDAR vs Scanning LiDAR
# ============================================================
content.append(para("4. Flash LiDAR vs. Scanning LiDAR", H2))

cmp_data = [
    ["項目", "Flash LiDAR", "Scanning LiDAR（機械走査型）"],
    ["照射方式", "広角フラッド照明（一括照射）", "点/線ビームを機械的に走査"],
    ["フレーム取得", "1 パルスで全画素同時取得\n（最大 30 fps 以上）", "ビーム走査完了後に1フレーム\n（高速回転ミラー等）"],
    ["可動部", "原則なし（ソリッドステート）", "回転ミラー・MEMS 等の可動部あり"],
    ["動体ブレ", "ほぼなし（全画素同時）", "走査中の動体に歪みが発生"],
    ["最大レンジ", "< 100 m（一般的）", "200 m 以上も可"],
    ["レーザー強度", "広角照射のためパルスエネルギーが大", "集中ビームのため相対的に低強度"],
    ["分解能", "2D 検出器アレイ数に依存\n（現状は比較的低め）", "走査角度精度で決まる\n（高分解能を達成しやすい）"],
    ["耐振動性", "高い", "可動部あり・振動に弱い"],
    ["コスト", "量産時に低コスト化の余地大", "機械部品コストが課題"],
    ["主な用途", "自動車後付センサー、ランディング\nドローン、AR/VR、ジェスチャー認識", "自動運転（Velodyne 等）\n地図作成・産業計測"],
]
cmp_table = Table(cmp_data, colWidths=[38*mm, 63*mm, 63*mm])
cmp_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
    ("GRID", (0, 0), (-1, -1), 0.3, colors.gray),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
content.append(cmp_table)
content.append(Spacer(1, 4*mm))

# ============================================================
# 5. 代表的な論文リスト
# ============================================================
content.append(PageBreak())
content.append(para("5. Flash LiDAR 基礎解説 ― 代表的な学術論文", H2))
content.append(para(
    "以下に、Flash LiDAR の構造・原理・比較に関する基礎的解説を含む代表的な論文を示す。"
    "信頼度検証（3票多数決）に基づいてフィルタリングし、確認できた情報のみを掲載している。"
))
content.append(Spacer(1, 3*mm))

papers = [
    {
        "no": "1",
        "title": "An Overview of Lidar Imaging Systems for Autonomous Vehicles",
        "authors": "Santiago Royo, Maria Ballesta-Garcia",
        "venue": "Applied Sciences, Vol. 9, No. 19, Art. 4093",
        "year": "2019",
        "doi": "10.3390/app9194093",
        "url": "https://www.mdpi.com/2076-3417/9/19/4093",
        "summary": (
            "自動運転向け LiDAR イメージングシステムの包括的入門レビュー。"
            "単点測距の基本原理（dToF / iToF / FMCW）から始まり、"
            "フラッシュ型・走査型・MEMS 型・OPA 型を比較解説。"
            "光源（パルス LD、VCSEL）と受光素子（APD、SPAD、SiPM）の"
            "特性も詳述しており、Flash LiDAR 入門に最適。"
        ),
        "relevance": "★★★★★ — Flash LiDAR 構造・原理・比較の基礎解説として最適",
    },
    {
        "no": "2",
        "title": "Data Processing Approaches on SPAD-Based d-TOF LiDAR Systems: A Review",
        "authors": "A. Maccarone et al.",
        "venue": "IEEE Sensors Journal, Vol. 21, No. 5",
        "year": "2020（掲載 2021）",
        "doi": "10.1109/JSEN.2020.3038487",
        "url": "https://ieeexplore.ieee.org/document/9261382/",
        "summary": (
            "SPAD ベースの直接 ToF Flash LiDAR システムにおける"
            "データ処理手法の体系的レビュー。"
            "SPAD アレイのハードウェア構成（各画素の TDC・カウンタ回路）、"
            "ヒストグラム蓄積処理、ピーク検出アルゴリズム、"
            "背景光抑圧手法を網羅的に解説。ADAS 応用における課題も論じる。"
        ),
        "relevance": "★★★★★ — SPAD ベース Flash LiDAR のセンサー構造と信号処理の最重要レビュー",
    },
    {
        "no": "3",
        "title": "Numerical Model of SPAD-Based Direct Time-of-Flight Flash LIDAR CMOS Image Sensors",
        "authors": "A. Tontini, L. Gasparini, M. Perenzoni",
        "venue": "Sensors, Vol. 20, No. 18, Art. 5203",
        "year": "2020",
        "doi": "10.3390/s20185203",
        "url": "https://www.mdpi.com/1424-8220/20/18/5203",
        "summary": (
            "SPAD ベース Flash LiDAR CMOS イメージセンサーの数値モデルを提案。"
            "照明光源・光学系・SPAD アレイの各ブロックをモデル化した"
            "モンテカルロシミュレーターを Matlab で実装し、"
            "背景雑音・ターゲット反射率の影響を定量評価。"
            "センサー構造の設計パラメータと測距精度の関係が明確に示されている。"
        ),
        "relevance": "★★★★☆ — Flash LiDAR システム全体の構成要素モデルとして参照価値高",
    },
    {
        "no": "4",
        "title": "SPADs and SiPMs Arrays for Long-Range High-Speed Light Detection and Ranging (LiDAR)",
        "authors": "F. Villa, F. Severini, F. Madonini, F. Zappa",
        "venue": "Sensors, Vol. 21, No. 11, Art. 3839",
        "year": "2021",
        "doi": "10.3390/s21113839",
        "url": "https://www.mdpi.com/1424-8220/21/11/3839",
        "summary": (
            "ポリテクニコ・ミラノによる SPAD・SiPM アレイの LiDAR 応用レビュー。"
            "Geiger モード APD の動作原理・クエンチング回路・アレイ構成を詳解し、"
            "Flash LiDAR（スキャナーレス 3D カメラ）における使用事例を解説。"
            "単一光子感度・ピコ秒タイミング・CMOS 集積化の観点から"
            "現状の課題と設計トレードオフを論じる。"
        ),
        "relevance": "★★★★★ — Flash LiDAR の受光素子構造（SPAD/SiPM）の基礎解説として最良",
    },
    {
        "no": "5",
        "title": "A Progress Review on Solid-State LiDAR and Nanophotonics-Based LiDAR Sensors",
        "authors": "Y. Li et al.",
        "venue": "Laser & Photonics Reviews, Vol. 16, No. 11, Art. 2100511",
        "year": "2022",
        "doi": "10.1002/lpor.202100511",
        "url": "https://onlinelibrary.wiley.com/doi/10.1002/lpor.202100511",
        "summary": (
            "ソリッドステート LiDAR（Flash 型含む）とナノフォトニクス応用の進展レビュー。"
            "MEMS 走査型・光フェーズドアレイ（OPA）・Flash 型を網羅的に比較。"
            "Flash LiDAR の照射・受光構造、ソリッドステート化のメリット、"
            "集積化技術（SoC 化、ウェーハ接合）に関する解説を含む。"
        ),
        "relevance": "★★★★☆ — ソリッドステート化の観点から Flash LiDAR を位置づける上で有用",
    },
    {
        "no": "6",
        "title": "A Review of SPAD Array Chip Design for Direct Time-of-Flight LiDAR",
        "authors": "（著者詳細は Discover Nano 誌掲載版を参照）",
        "venue": "Discover Nano (Springer Nature), Art. s11671-026-04493-x",
        "year": "2026",
        "doi": "10.1186/s11671-026-04493-x",
        "url": "https://link.springer.com/article/10.1186/s11671-026-04493-x",
        "summary": (
            "dToF LiDAR 向け SPAD アレイチップ設計の最新レビュー（2026年）。"
            "ヒストグラムフリー測距・可変ヒストグラム分解能・"
            "干渉耐性・精度最適化・PPA（電力・性能・面積）設計最適化を論じる。"
            "Flash LiDAR のオンチップ処理アーキテクチャの現状を把握する上で最新資料。"
        ),
        "relevance": "★★★★☆ — Flash LiDAR チップ設計の最新動向として参照価値高",
    },
    {
        "no": "7",
        "title": "Imaging Flash Lidar for Autonomous Safe Landing and Spacecraft Proximity Operations",
        "authors": "Farzin Amzajerdian et al. (NASA Langley Research Center)",
        "venue": "SPIE Proceedings (Laser Radar Technology and Applications XXI)",
        "year": "2016",
        "doi": "NASA-TM-20160011575",
        "url": "https://ntrs.nasa.gov/api/citations/20160011575/downloads/20160011575.pdf",
        "summary": (
            "NASA ラングレー研究センターによる Flash LiDAR の飛行試験報告。"
            "16k 画素レンジ画像を 20 Hz・最大 1800 m スラントレンジで取得するシステムを解説。"
            "送光部（パルスレーザー）・受光部（Focal Plane Array）・"
            "タイミング回路の構成が具体的に記述されており、"
            "実装事例として参照価値が高い。"
        ),
        "relevance": "★★★☆☆ — 実装システムの構成要素把握に有用（宇宙応用事例）",
    },
    {
        "no": "8",
        "title": "Enhancing Resolution for Flash LiDAR with Multi-View Imaging Optics and Range Image Tiling",
        "authors": "（著者詳細は Sensors 誌掲載版を参照）",
        "venue": "Sensors, Vol. 25, No. 11, Art. 3288",
        "year": "2025",
        "doi": "10.3390/s25113288",
        "url": "https://www.mdpi.com/1424-8220/25/11/3288",
        "summary": (
            "Flash LiDAR の低分解能という制約を多視点撮像光学系で克服する手法を提案。"
            "Flash LiDAR の基本構成（フラッド照明＋FPA）を前提とした上で、"
            "分解能向上のためのレンジ画像タイリング手法を解説。"
            "2D アレイ検出器の分解能制約とその対処法を理解する上で有用。"
        ),
        "relevance": "★★★☆☆ — Flash LiDAR の構造的制約（解像度）の理解に有用",
    },
]

for p in papers:
    # Paper header
    content.append(para(
        f"<b>[{p['no']}] {p['title']}</b>",
        style("Normal", fontSize=10, textColor=colors.HexColor("#1a3a5c"), spaceAfter=2)
    ))
    meta_data = [
        ["著者", p["authors"]],
        ["掲載誌/会議", p["venue"]],
        ["発行年", p["year"]],
        ["DOI", p["doi"]],
        ["URL", p["url"]],
    ]
    meta_table = Table(meta_data, colWidths=[22*mm, 140*mm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    content.append(meta_table)
    content.append(para(f"<i>概要：</i>{p['summary']}", BODY))
    content.append(para(f"<i>関連度：</i>{p['relevance']}", CAPTION))
    content.append(hr())

# ============================================================
# 6. 検索・参照したソース一覧
# ============================================================
content.append(para("6. 参照ソース一覧", H2))
sources = [
    ("ResearchGate", "Data Processing Approaches on SPAD-based Flash LiDAR Systems: A Review",
     "https://www.researchgate.net/publication/347005301"),
    ("ResearchGate", "A Review of LiDAR sensor Technologies for Perception in Automated Driving",
     "https://www.researchgate.net/publication/366152578"),
    ("MDPI Applied Sciences", "An Overview of Lidar Imaging Systems for Autonomous Vehicles",
     "https://www.mdpi.com/2076-3417/9/19/4093"),
    ("MDPI Sensors", "SPADs and SiPMs Arrays for Long-Range High-Speed LiDAR",
     "https://www.mdpi.com/1424-8220/21/11/3839"),
    ("Wiley / Laser & Photonics Reviews", "A Progress Review on Solid-State LiDAR",
     "https://onlinelibrary.wiley.com/doi/10.1002/lpor.202100511"),
    ("IEEE Xplore", "Data Processing Approaches on SPAD-Based d-TOF LiDAR: A Review",
     "https://ieeexplore.ieee.org/document/9261382/"),
    ("Springer Nature / Discover Nano", "A Review of SPAD Array Chip Design for dToF LiDAR",
     "https://link.springer.com/article/10.1186/s11671-026-04493-x"),
    ("PMC / Sensors 2020", "Numerical Model of SPAD-Based Direct ToF Flash LIDAR",
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC7571262/"),
    ("NASA NTRS", "Imaging Flash Lidar for Autonomous Safe Landing",
     "https://ntrs.nasa.gov/api/citations/20160011575"),
    ("MDPI Sensors 2025", "Enhancing Resolution for Flash LiDAR",
     "https://www.mdpi.com/1424-8220/25/11/3288"),
    ("Semantic Scholar", "Numerical Model of SPAD-Based Direct ToF Flash LIDAR",
     "https://www.semanticscholar.org/paper/Numerical-Model-of-SPAD-Based-Direct-Time-of-Flight-Tontini-Gasparini/3c26bedd4e289374ee62ab04b4676604ad225bee"),
]
for idx, (src, title, url) in enumerate(sources, 1):
    content.append(para(
        f"[S{idx}] {src} — {title}<br/><font color='#2255aa'>{url}</font>",
        CAPTION
    ))
    content.append(Spacer(1, 1*mm))

# ============================================================
# Build PDF
# ============================================================
doc = SimpleDocTemplate(
    OUTPUT_PATH,
    pagesize=A4,
    leftMargin=20*mm,
    rightMargin=20*mm,
    topMargin=20*mm,
    bottomMargin=20*mm,
    title="Flash LiDAR 技術調査レポート",
    author="Claude Research Agent",
    subject="Flash LiDAR 構造・構成 基礎解説論文サーベイ",
)
doc.build(content)
print(f"PDF saved: {OUTPUT_PATH}")
