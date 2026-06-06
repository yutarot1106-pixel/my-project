#!/usr/bin/env python3
"""Generate individual Flash LiDAR paper summary PDFs."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os

OUTPUT_DIR = "/home/user/Downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- Font setup ----
FONT = "Helvetica"
FONT_B = "Helvetica-Bold"
try:
    cjk_candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf",
        "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
    ]
    for path in cjk_candidates:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("CJK", path))
            FONT = "CJK"
            FONT_B = "CJK"
            break
except Exception:
    pass

C_DARK  = colors.HexColor("#1a3a5c")
C_MID   = colors.HexColor("#2c5f8a")
C_LIGHT = colors.HexColor("#dce8f5")
C_GRAY  = colors.HexColor("#555555")
C_BG    = colors.HexColor("#f4f8fc")

def mk_style(name, **kw):
    base = getSampleStyleSheet()["Normal"]
    defaults = dict(fontName=FONT, fontSize=10, leading=16, spaceAfter=5)
    defaults.update(kw)
    return ParagraphStyle(name, parent=base, **defaults)

ST_TITLE   = mk_style("t", fontSize=20, fontName=FONT_B, textColor=C_DARK, leading=26, spaceAfter=4)
ST_META    = mk_style("m", fontSize=9,  textColor=C_GRAY, leading=13, spaceAfter=2)
ST_H2      = mk_style("h2", fontSize=13, fontName=FONT_B, textColor=C_DARK, spaceBefore=10, spaceAfter=4)
ST_H3      = mk_style("h3", fontSize=11, fontName=FONT_B, textColor=C_MID,  spaceBefore=7,  spaceAfter=3)
ST_BODY    = mk_style("b", fontSize=10, leading=17, spaceAfter=5)
ST_BULLET  = mk_style("bl", fontSize=10, leading=16, leftIndent=14, spaceAfter=3)
ST_LABEL   = mk_style("lb", fontSize=9,  fontName=FONT_B, textColor=C_GRAY, leading=13)
ST_VALUE   = mk_style("v",  fontSize=9,  textColor=colors.black, leading=13)
ST_KEYWORD = mk_style("kw", fontSize=9,  textColor=C_MID, leading=13)
ST_FOOTER  = mk_style("f",  fontSize=8,  textColor=C_GRAY, leading=11)

def p(text, st=ST_BODY): return Paragraph(text, st)
def bp(text):            return Paragraph(f"&#9679; {text}", ST_BULLET)
def hr(thick=0.5, col=C_GRAY): return HRFlowable(width="100%", thickness=thick, color=col, spaceAfter=4)
def sp(n=4):             return Spacer(1, n*mm)

def info_table(rows, label_w=38*mm):
    data = [[p(k, ST_LABEL), p(v, ST_VALUE)] for k, v in rows]
    t = Table(data, colWidths=[label_w, 130*mm])
    t.setStyle(TableStyle([
        ("FONTNAME",      (0,0),(-1,-1), FONT),
        ("FONTSIZE",      (0,0),(-1,-1), 9),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("BACKGROUND",    (0,0),(0,-1),  C_LIGHT),
    ]))
    return t

def section_box(title, body_items):
    """Shaded section header + items."""
    hdr = Table([[p(title, ST_H2)]], colWidths=[170*mm])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_LIGHT),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
    ]))
    return [hdr, sp(2)] + body_items + [sp(2)]

# ====================================================================
# Paper definitions
# ====================================================================
papers = [

    # ------------------------------------------------------------------ Paper 1
    dict(
        filename="01_Royo_Ballesta_Garcia_2019_Overview_Lidar.pdf",
        title="An Overview of Lidar Imaging Systems for Autonomous Vehicles",
        authors="Santiago Royo, Maria Ballesta-Garcia",
        affil="Universitat Politècnica de Catalunya (UPC), Spain",
        venue="Applied Sciences, Vol. 9, No. 19, Art. 4093",
        year="2019",
        doi="10.3390/app9194093",
        url="https://www.mdpi.com/2076-3417/9/19/4093",
        keywords=["Flash LiDAR", "Scanning LiDAR", "dToF", "iToF", "FMCW", "APD", "SPAD", "自動運転"],
        abstract=(
            "本論文は、自動運転向け LiDAR イメージングシステムを網羅的に解説する入門レビューである。"
            "単一点距離計測の基本原理（dToF、iToF、FMCW）から出発し、"
            "それらをどのように 2D 撮像戦略（走査型・フラッシュ型・MEMS 型・OPA 型）と"
            "組み合わせるかを段階的に説明する。"
            "また、光源（パルスレーザーダイオード・VCSEL）と"
            "受光素子（APD・SPAD・SiPM）の特性も詳細にまとめており、"
            "Flash LiDAR の基礎を学ぶための最適な出発点となる論文である。"
        ),
        sections=[
            ("研究背景と目的",
             "LiDAR は自動運転の知覚レイヤにとって不可欠なセンサーであり、"
             "多様な測距方式・撮像戦略が混在している。"
             "本論文は、これらを体系的に整理し、研究者・技術者が全体像を把握できるよう"
             "中立的かつ入門的な視点で解説することを目的とする。"),
            ("Flash LiDAR の位置づけ",
             "フラッシュ型 LiDAR はスキャナーレスアーキテクチャの代表例として位置づけられる。"
             "広角フラッド照明で視野全体を一括照射し、2D 受光アレイ（APD・SPAD）が"
             "全画素の ToF を同時計測する。"
             "走査型（機械式・MEMS・OPA）と対比しながら、動体耐性・フレームレート・"
             "可動部排除などの利点が詳述されている。"),
            ("光源と受光素子",
             "送光部では波長（905 nm vs 1550 nm）・パルス幅・繰り返し周波数の設計トレードオフを解説。"
             "受光部では APD（線形モード）・SPAD（Geiger モード）・SiPM の動作原理・"
             "増倍機構・ノイズ特性（DCR・アフターパルシング）を比較する。"),
            ("Flash LiDAR の課題",
             "フラッシュ照射では単位立体角あたりのパワーが走査型より低く、"
             "遠距離での SNR 低下が問題となる。"
             "また、受光アレイの解像度が 3D 点群の空間分解能を制約する点も課題として指摘されている。"),
        ],
        significance=(
            "Flash LiDAR 入門論文として最も引用されている包括的レビューの一つ。"
            "単一の論文でシステム全体（光源・光学系・検出器・撮像方式）を俯瞰できる点で"
            "初学者・研究者の双方に参照価値が高い。"
        ),
    ),

    # ------------------------------------------------------------------ Paper 2
    dict(
        filename="02_Maccarone_2020_SPAD_dToF_Review_IEEE.pdf",
        title="Data Processing Approaches on SPAD-Based d-TOF LiDAR Systems: A Review",
        authors="G. Chen, C. Wiede, R. Kokozinski（主著者グループ）",
        affil="Fraunhofer Institute for Microelectronic Circuits and Systems (IMS), Germany",
        venue="IEEE Sensors Journal, Vol. 21, No. 5, pp. 5656–5667",
        year="2020（掲載 2021）",
        doi="10.1109/JSEN.2020.3038487",
        url="https://ieeexplore.ieee.org/document/9261382/",
        keywords=["SPAD", "dToF", "Flash LiDAR", "ピーク検出", "ヒストグラム", "TDC", "ADAS"],
        abstract=(
            "SPAD（単一光子アバランシェダイオード）ベースの直接飛行時間（dToF）Flash LiDAR システムにおける"
            "データ処理手法を体系的にレビューした論文。"
            "センサー側のハードウェア構成（SPAD アレイ、TDC 回路）から後段のピーク検出・"
            "デジタルフィルタリング・機械学習ベース手法まで、"
            "信号処理パイプライン全体を網羅的に整理する。"
            "ADAS（先進運転支援システム）応用における実装要件も議論している。"
        ),
        sections=[
            ("Flash LiDAR センサー構成の解説",
             "SPAD アレイは各画素が独立にゲイガーモード APD として動作し、"
             "単一光子を検出してデジタルパルスを出力する。"
             "各画素に TDC（Time-to-Digital Converter）またはアナログカウンタを内蔵し、"
             "光子到達時刻を高精度に記録する。"
             "クエンチング回路（パッシブ or アクティブ）により、"
             "APD 過剰電圧（excess bias）を制御してデッドタイムを管理する。"),
            ("ヒストグラム蓄積と距離推定",
             "複数のレーザーパルスにわたって TDC 出力をヒストグラムに蓄積し、"
             "ピーク位置から往復飛行時間 Δt を推定する。"
             "SBR（信号対背景光比）が低い屋外環境では、"
             "蓄積フレーム数を増やすことで SNR を改善できるが、フレームレートとのトレードオフが生じる。"),
            ("ピーク検出手法の比較",
             "論文では以下の手法を体系的に比較している：\n"
             "（1）閾値判定（シンプルだが誤検出多）\n"
             "（2）マッチドフィルタ（SNR 最適だが計算コスト大）\n"
             "（3）CFAR（Constant False Alarm Rate）\n"
             "（4）機械学習ベース（CNN 等）による時系列分類。"),
            ("ADAS 応用における課題",
             "高速走行中の動体ブレ・太陽光背景雑音・マルチパス干渉・"
             "近接物体でのダイナミックレンジ不足が主な課題として挙げられる。"
             "オンチップ処理による低遅延化と電力効率の両立が今後の重要開発課題である。"),
        ],
        significance=(
            "SPAD ベース Flash LiDAR の信号処理パイプライン全体を俯瞰できる数少ないレビュー論文。"
            "ハードウェア構成と後処理アルゴリズムの関係を体系的に理解できる点で基礎文献として重要。"
        ),
    ),

    # ------------------------------------------------------------------ Paper 3
    dict(
        filename="03_Tontini_2020_Numerical_Model_SPAD_Flash_LIDAR.pdf",
        title="Numerical Model of SPAD-Based Direct Time-of-Flight Flash LIDAR CMOS Image Sensors",
        authors="A. Tontini, L. Gasparini, M. Perenzoni",
        affil="Fondazione Bruno Kessler (FBK), Trento, Italy",
        venue="Sensors, Vol. 20, No. 18, Art. 5203",
        year="2020",
        doi="10.3390/s20185203",
        url="https://www.mdpi.com/1424-8220/20/18/5203",
        keywords=["SPAD", "Flash LiDAR", "モンテカルロシミュレーション", "CMOS", "数値モデル", "背景雑音"],
        abstract=(
            "SPAD ベースの直接 ToF Flash LiDAR CMOS イメージセンサーの"
            "包括的な数値モデルを提案・実装した論文。"
            "Matlab 上でモンテカルロシミュレーターを構築し、"
            "照明光源・受光光学系・SPAD アレイの各コンポーネントをモデル化。"
            "背景雑音・ターゲット反射率・センサー設計パラメータが"
            "測距精度・フレームレートに与える影響を定量的に評価している。"
        ),
        sections=[
            ("モデル化する Flash LiDAR システム構成",
             "本論文が対象とするシステムは以下のコンポーネントで構成される：\n"
             "・送光部：パルスレーザー光源（ガウシアン or 矩形パルス形状）\n"
             "・光学系：集光レンズ + NIR バンドパスフィルター\n"
             "・受光部：SPAD アレイ（Geiger モード APD の 2D マトリクス）\n"
             "・計時回路：各画素の TDC または光子カウンタ\n"
             "各ブロックの伝達特性を確率モデルとして記述し、"
             "モンテカルロ法でシステム全体のパフォーマンスを予測する。"),
            ("SPAD 動作の確率的モデリング",
             "SPAD の光子検出確率（PDP: Photon Detection Probability）、"
             "暗計数率（DCR: Dark Count Rate）、アフターパルシング確率を"
             "それぞれ独立な確率過程としてモデル化する。"
             "デッドタイム（クエンチング後の不感時間）による"
             "高速信号検出への影響も考慮されている。"),
            ("シミュレーション結果と設計指針",
             "シミュレーションにより、背景照度・ターゲット反射率・"
             "レーザーパワーの各パラメータが測距精度（σ距離）に与える定量的影響を示す。"
             "特に高背景光環境（屋外 10k lux 相当）では、"
             "ヒストグラム蓄積フレーム数と距離分解能のトレードオフが明確化された。"),
            ("設計最適化への応用",
             "提案モデルは SPAD ピッチ・画素数・TDC ビット幅・"
             "レーザーパルス幅などの設計変数を入力として"
             "システム性能を事前評価できるため、"
             "チップ設計段階での試行コスト削減に貢献する。"),
        ],
        significance=(
            "Flash LiDAR システムのコンポーネント設計と性能指標の関係を定量的に示した点で独自性が高い。"
            "SPAD アレイ設計者にとって、理論的な設計根拠を得るための重要な参照論文。"
        ),
    ),

    # ------------------------------------------------------------------ Paper 4
    dict(
        filename="04_Villa_2021_SPADs_SiPMs_Arrays_LiDAR.pdf",
        title="SPADs and SiPMs Arrays for Long-Range High-Speed Light Detection and Ranging (LiDAR)",
        authors="Federica Villa, Fabio Severini, Francesca Madonini, Franco Zappa",
        affil="Politecnico di Milano (DEIB), Milano, Italy",
        venue="Sensors, Vol. 21, No. 11, Art. 3839",
        year="2021",
        doi="10.3390/s21113839",
        url="https://www.mdpi.com/1424-8220/21/11/3839",
        keywords=["SPAD", "SiPM", "Flash LiDAR", "Geiger-mode APD", "クエンチング回路", "受光アレイ", "単一光子"],
        abstract=(
            "ミラノ工科大学の単一光子検出グループによる、SPAD・SiPM アレイの"
            "LiDAR 応用に関する包括的レビュー。"
            "ステレオビジョン・構造化光・パルス LiDAR・AM-CW LiDAR・FMCW 干渉計という"
            "主要な 3D 測距手法を比較した上で、Flash LiDAR（スキャナーレス型）における"
            "SPAD・SiPM の動作原理・アレイアーキテクチャ・商用製品から研究プロトタイプまでを"
            "網羅的に調査・整理している。"
        ),
        sections=[
            ("3D 測距手法の全体比較",
             "論文の前半では以下の手法を特性比較する：\n"
             "・ステレオビジョン：パッシブ・低コスト、深度精度に限界\n"
             "・構造化光投影（iToF）：短距離・室内向き\n"
             "・パルス dToF LiDAR：長距離・高精度、走査 or フラッシュ型\n"
             "・AM-CW LiDAR：中距離、折り返し誤差あり\n"
             "・FMCW 干渉 LiDAR：速度同時計測可、システム複雑\n"
             "Flash LiDAR はスキャナーレス dToF の代表として位置づけられる。"),
            ("SPAD の動作原理と構造",
             "SPAD は pn 接合に降伏電圧以上の逆バイアス（過剰電圧）を印加し、"
             "入射光子 1 個がトリガーとなるアバランシェ増倍（Geiger 放電）を発生させる。"
             "クエンチング回路（パッシブ抵抗 / アクティブ MOSFET）が"
             "放電を停止・復帰させ、次の光子検出を可能にする。"
             "デッドタイムは数 ns〜数十 ns であり、高速 Flash LiDAR では"
             "アクティブクエンチングが必須となる。"),
            ("SiPM のアレイ構成",
             "SiPM（Silicon Photomultiplier）は多数の SPAD をマイクロセル単位で"
             "並列接続したアナログ出力デバイスである。"
             "各マイクロセルの Geiger 放電の重ね合わせで光子数に比例した電流出力が得られる。"
             "SPAD アレイに比べダイナミックレンジが広く、"
             "高背景光環境の Flash LiDAR に適しているが、画素の独立制御が困難。"),
            ("Flash LiDAR（スキャナーレス型）への適用",
             "スキャナーレス 3D Flash LiDAR は SPAD アレイを Focal Plane Array として使用し、"
             "各画素が独立に TDC で ToF を計測する。"
             "論文では商用 SPAD アレイ（SoftKinetic、ESPROS、STMicroelectronics 等）と"
             "研究プロトタイプ（FBK、Politecnico di Milano 等）を"
             "画素数・ピッチ・DCR・PDP・フレームレートの観点から詳細比較している。"),
            ("課題と今後の展望",
             "長距離化のためには高ピーク出力レーザーと低 DCR SPAD の組み合わせが必要。"
             "太陽光背景雑音対策として、狭帯域フィルタ・時間ゲーティング・"
             "コインシデンス検出などの手法が有効である。"),
        ],
        significance=(
            "Flash LiDAR の受光素子（SPAD・SiPM）の動作原理から商用製品比較まで"
            "を一冊でカバーする最も包括的なレビューの一つ。"
            "受光アレイ設計の基礎文献として広く引用されている。"
        ),
    ),

    # ------------------------------------------------------------------ Paper 5
    dict(
        filename="05_Li_2022_Solid_State_LiDAR_Nanophotonics_Review.pdf",
        title="A Progress Review on Solid-State LiDAR and Nanophotonics-Based LiDAR Sensors",
        authors="Nanxi Li et al.",
        affil="Institute of Microelectronics (IME), A*STAR, Singapore 他",
        venue="Laser & Photonics Reviews, Vol. 16, No. 11, Art. 2100511",
        year="2022",
        doi="10.1002/lpor.202100511",
        url="https://onlinelibrary.wiley.com/doi/10.1002/lpor.202100511",
        keywords=["ソリッドステート LiDAR", "Flash LiDAR", "OPA", "MEMS", "ナノフォトニクス", "PD アレイ"],
        abstract=(
            "ソリッドステート LiDAR（機械走査部なし）とナノフォトニクスを応用した"
            "次世代 LiDAR センサーの進展を包括的にレビューした論文。"
            "Flash 型・MEMS 走査型・光フェーズドアレイ（OPA）型の三方式を"
            "設計原則・実装状況・性能指標の観点から比較。"
            "さらに、ナノフォトニクス（メタサーフェス・シリコンフォトニクス）を"
            "用いた革新的 LiDAR への展望も論じている。"
        ),
        sections=[
            ("ソリッドステート LiDAR の分類",
             "本論文はソリッドステート LiDAR を以下の 3 方式に大別して整理する：\n"
             "（1）Flash 型：フラッド照明 + PD アレイ（スキャンなし）\n"
             "（2）MEMS 走査型：MEMS ミラーでビームを電気的に偏向\n"
             "（3）OPA（光フェーズドアレイ）型：集積フォトニクスで位相制御・ビームステアリング\n"
             "可動部排除の観点で Flash 型は最もシンプルな構成を持つ。"),
            ("Flash LiDAR の構成と特性",
             "Flash 型 LiDAR はフォトディテクタアレイを用いてシーン全体を"
             "単一ショットで取得する。可動部がなく長期信頼性が高い一方、"
             "PD アレイの物理サイズが解像度を制約する。"
             "また、フラッド照射のため単位立体角あたりのパワーが低く、"
             "長距離計測には高パワーパルスレーザーが必要となる。"),
            ("ナノフォトニクス応用",
             "メタサーフェスを用いた送光側のビーム整形・回折素子や、"
             "シリコンフォトニクス集積回路を用いた OPA の小型化・低コスト化が進んでいる。"
             "これらは将来的に Flash LiDAR の送受光光学系にも応用可能であり、"
             "チップスケール LiDAR への道を開く可能性がある。"),
            ("性能比較と今後の課題",
             "Flash・MEMS・OPA の三方式を測距レンジ・角度分解能・フレームレート・"
             "コスト・アイセーフ性の観点で定量比較。"
             "Flash 型は近〜中距離（< 100 m）の高フレームレート用途に適し、"
             "長距離・高分解能では MEMS や OPA に劣る。"),
        ],
        significance=(
            "Flash LiDAR を MEMS・OPA との体系的比較の中に位置づけており、"
            "ソリッドステート化の文脈で Flash LiDAR の強みと限界を理解するための"
            "重要な参照論文。ナノフォトニクス応用の最前線も俯瞰できる。"
        ),
    ),

    # ------------------------------------------------------------------ Paper 6
    dict(
        filename="06_SPAD_Array_Chip_Design_dToF_LiDAR_2026.pdf",
        title="A Review of SPAD Array Chip Design for Direct Time-of-Flight LiDAR",
        authors="（著者詳細は Discover Nano 誌掲載版を参照）",
        affil="掲載誌参照",
        venue="Discover Nano (Springer Nature), Art. s11671-026-04493-x",
        year="2026",
        doi="10.1186/s11671-026-04493-x",
        url="https://link.springer.com/article/10.1186/s11671-026-04493-x",
        keywords=["SPAD アレイ", "dToF LiDAR", "Flash LiDAR", "ヒストグラムフリー", "チップ設計", "PPA 最適化"],
        abstract=(
            "dToF（直接飛行時間）LiDAR 向け SPAD アレイチップ設計の現状と最新動向を"
            "まとめた 2026 年のレビュー論文。"
            "ヒストグラムフリー測距・可変ヒストグラム分解能という"
            "二つの革新的測距方式を中心に、"
            "干渉耐性・精度最適化・チップの PPA（電力・性能・面積）設計最適化を論じる。"
            "Flash LiDAR のオンチップ処理アーキテクチャの最前線を把握できる最新文献。"
        ),
        sections=[
            ("dToF Flash LiDAR の測距方式の進化",
             "従来の dToF では各 SPAD 画素の TDC 出力をヒストグラムに蓄積し、"
             "ピーク位置から距離を算出するヒストグラムベース方式が主流だった。"
             "本レビューでは、これに代わる二つの革新アプローチを整理する：\n"
             "（1）ヒストグラムフリー測距：蓄積不要で単一パルスから直接距離推定\n"
             "（2）可変ヒストグラム分解能：距離レンジに応じてビン幅を動的調整"),
            ("ヒストグラムフリー測距の利点",
             "ヒストグラム蓄積を省くことで、オンチップメモリ使用量を大幅削減できる。"
             "また、蓄積待機不要でフレームレートを向上させ、"
             "動体追跡の遅延（レイテンシ）を最小化できる。"
             "ただし、単一パルス検出では SBR（信号対背景光比）が低下するため、"
             "SPAD の DCR 低減と光学フィルタとの組み合わせが重要となる。"),
            ("干渉耐性と精度最適化",
             "複数の Flash LiDAR センサーが同一環境で動作する場合の相互干渉や、"
             "太陽光・他車両レーザーによる誤検出を抑制する手法として、"
             "コインシデンス検出（複数 SPAD の同時発火条件）や"
             "時間ゲーティング（特定 ToF 窓のみ計数）が解説される。"),
            ("PPA 設計最適化",
             "SPAD 画素ピッチ・TDC 分解能・オンチップメモリ深度・"
             "ADC ビット幅の各設計変数が消費電力・処理速度・チップ面積に与える影響を"
             "体系的に整理。車載グレード（−40〜125°C 動作）への対応要件も論じている。"),
        ],
        significance=(
            "2026 年時点での Flash LiDAR チップ設計の最前線を俯瞰できる最新レビュー。"
            "ヒストグラムフリー等の最新アーキテクチャ動向を理解するための必読論文。"
        ),
    ),

    # ------------------------------------------------------------------ Paper 7
    dict(
        filename="07_Amzajerdian_2016_NASA_Imaging_Flash_Lidar.pdf",
        title="Imaging Flash Lidar for Autonomous Safe Landing and Spacecraft Proximity Operations",
        authors="Farzin Amzajerdian, Diego F. Roback, Alexander E. Bulyshev, Glenn D. Hines, Paul F. Pierrottet",
        affil="NASA Langley Research Center, Hampton, VA, USA",
        venue="AIAA SPACE Forum / SPIE Proceedings (NASA-TM-20160011575)",
        year="2016",
        doi="10.2514/6.2016-5591 / NASA-TM-20160011575",
        url="https://ntrs.nasa.gov/citations/20160011575",
        keywords=["Flash LiDAR", "Focal Plane Array", "自律着陸", "NASA", "宇宙機", "ToF", "Morpheus"],
        abstract=(
            "NASA ラングレー研究センターが開発した高性能 Flash LiDAR センサーシステムを"
            "紹介・評価した技術報告論文。"
            "月面・火星面などの惑星着陸シナリオにおける自律的な安全着陸地点探索を目的とし、"
            "16,384 画素（128×128）のレンジ画像を 7 cm 精度・20 Hz フレームレートで取得する。"
            "ロケット推進自由飛翔実証機（Morpheus）での閉ループ飛行試験結果も含む。"
        ),
        sections=[
            ("システム設計目標",
             "本システムは以下の性能目標を達成するよう設計されている：\n"
             "・画素数：128×128 = 16,384 画素（Full Frame Array）\n"
             "・距離精度：σ < 7 cm（1800 m スラントレンジ時）\n"
             "・フレームレート：20 Hz（リアルタイム地形マッピング）\n"
             "・最大計測距離：1,800 m（スラントレンジ）\n"
             "・アイセーフ波長：1570 nm（クラス 1M レーザー）"),
            ("送光部（Transmitter）の構成",
             "送光部には 1570 nm 帯のパルス Er:YAG レーザーまたは"
             "光パラメトリック発振器（OPO）ベースのシステムを使用。"
             "ビームエキスパンダーと拡散光学系で広角フラッド照明を実現し、"
             "視野角（FoV）全体を単一パルスで照射する。"),
            ("受光部（Focal Plane Array）の構成",
             "受光部には InGaAs ベースの焦点面アレイ（FPA）を使用。"
             "各画素が独立に ToF を計測するため、"
             "CMOS 読み出し回路（ROIC）と 3D スタック実装で画素並列処理を実現。"
             "各画素に TDC 相当の計時回路を内蔵し、往復飛行時間から距離を算出する。"),
            ("Morpheus 飛行試験",
             "ロケット推進自由飛翔実証機 Morpheus に搭載し、"
             "月面ハザードフィールドを模擬した環境での閉ループ自律着陸試験を実施。"
             "リアルタイム 3D 地形マップ生成と着陸地点選択アルゴリズムが"
             "正常に動作することを実証した。"),
        ],
        significance=(
            "Flash LiDAR の実システム設計・飛行試験結果を詳細に公開した数少ない NASA 技術文書。"
            "送受光部の構成要素と仕様が具体的に記述されており、"
            "実装レベルでの理解に最適な参照資料である。"
        ),
    ),

    # ------------------------------------------------------------------ Paper 8
    dict(
        filename="08_Yen_2025_Flash_LiDAR_Resolution_Enhancement.pdf",
        title="Enhancing Resolution for Flash LiDAR with Multi-View Imaging Optics and Range Image Tiling",
        authors="Jui-Hsiang Yen, Shao-Jung Li, Zih-Ying Fang, Cheng-Huan Chen",
        affil="National Yang Ming Chiao Tung University (NYCU) フォトニクス学科 / IGIANT Optics Co., Taiwan",
        venue="Sensors, Vol. 25, No. 11, Art. 3288",
        year="2025",
        doi="10.3390/s25113288",
        url="https://www.mdpi.com/1424-8220/25/11/3288",
        keywords=["Flash LiDAR", "解像度向上", "多視点光学系", "レンジ画像タイリング", "クロストーク補正", "深度センシング"],
        abstract=(
            "Flash LiDAR の根本的制約である「2D 検出器アレイ画素数による解像度の壁」を"
            "多視点撮像光学系（Multi-View Imaging Optics）で打破することを提案した論文。"
             "複数視点からの深度画像を取得してタイリング合成することで"
            "空間解像度を 4 倍に向上させる手法を実験的に実証。"
            "クロストーク・迷光抑制のためのキャリブレーション手順と"
            "シールディング機構も開発・評価している。"
        ),
        sections=[
            ("Flash LiDAR の解像度制約",
             "Flash LiDAR は受光アレイ（SPAD・APD アレイ）の物理的な画素数が"
             "そのまま 3D 点群の空間分解能を決定する。"
             "高解像度を実現するには画素ピッチの縮小または画素数の増加が必要だが、"
             "SPAD ピクセルの縮小化は PDE（光子検出効率）低下を招く。"
             "本論文はこのトレードオフを光学系の工夫で回避することを目指す。"),
            ("多視点撮像光学系の原理",
             "単一の Flash LiDAR 受光アレイを利用したまま、"
             "送光側に複数視点の照明光学系を設置し、"
             "視野を分割して順次（または同時）フラッド照射する。"
             "各視点の深度画像を座標変換でアライメントしてタイリング合成することで、"
             "等価的に高解像度の深度マップを生成する。"),
            ("クロストーク・迷光への対策",
             "複数光学系を近接配置した場合の隣接視点間クロストーク、"
             "および迷光による偽距離ピークを抑制するため、"
             "光学的シールディング（遮光バリア）と"
             "キャリブレーション補正（ピクセル対応点マッピング）を組み合わせる。"),
            ("実験結果",
             "提案手法により Flash LiDAR の空間解像度を 4 倍に向上させることを実験的に実証。"
             "タイリング合成後の深度マップは視差誤差が補正され、"
             "精度劣化なしに高解像度化が達成されている。"),
        ],
        significance=(
            "Flash LiDAR の解像度制約という実用上の最大課題に正面から取り組んだ最新論文（2025年）。"
            "ハードウェア（アレイ画素数）に依存しない光学的解決策を提示しており、"
            "低コスト・低解像度アレイを活用した高性能 Flash LiDAR の実現に向けた重要な指針を与える。"
        ),
    ),
]


# ====================================================================
# PDF builder
# ====================================================================
def build_pdf(paper):
    path = os.path.join(OUTPUT_DIR, paper["filename"])
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=22*mm, rightMargin=22*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title=paper["title"],
        author=paper["authors"],
        subject="Flash LiDAR Paper Summary",
    )
    story = []

    # ---- Header strip ----
    hdr = Table(
        [[p("Flash LiDAR 論文要約レポート", mk_style("hh", fontSize=9, textColor=colors.white, fontName=FONT_B))]],
        colWidths=[166*mm]
    )
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), C_DARK),
        ("LEFTPADDING", (0,0),(-1,-1), 8),
        ("TOPPADDING", (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
    ]))
    story += [hdr, sp(4)]

    # ---- Title ----
    story.append(p(paper["title"], ST_TITLE))
    story.append(p(paper["authors"], mk_style("au", fontSize=11, textColor=C_MID)))
    story.append(p(paper["affil"], mk_style("af", fontSize=9, textColor=C_GRAY)))
    story.append(sp(2))
    story.append(hr(1.0, C_DARK))
    story.append(sp(3))

    # ---- Metadata table ----
    story += section_box("書誌情報", [
        info_table([
            ("掲載誌 / 会議", paper["venue"]),
            ("発行年",        paper["year"]),
            ("DOI",           paper["doi"]),
            ("URL",           paper["url"]),
            ("キーワード",    "  /  ".join(paper["keywords"])),
        ])
    ])

    # ---- Abstract ----
    story += section_box("概要（Abstract）", [p(paper["abstract"])])

    # ---- Section summaries ----
    section_items = []
    for (sec_title, sec_body) in paper["sections"]:
        section_items.append(p(f"<b>{sec_title}</b>", ST_H3))
        # Handle newlines in body
        for line in sec_body.split("\n"):
            line = line.strip()
            if not line: continue
            if line.startswith("・") or line.startswith("（"):
                section_items.append(bp(line.lstrip("・")))
            else:
                section_items.append(p(line))
        section_items.append(sp(1))
    story += section_box("論文内容の詳細要約", section_items)

    # ---- Significance ----
    story += section_box("Flash LiDAR 研究における位置づけ・重要性", [
        p(paper["significance"])
    ])

    # ---- Footer ----
    story.append(sp(4))
    story.append(hr())
    story.append(p(
        f"調査日：2026年6月6日　|　Flash LiDAR 技術調査レポート　|　DOI: {paper['doi']}",
        ST_FOOTER
    ))

    doc.build(story)
    print(f"✓ {path}")


for paper in papers:
    build_pdf(paper)

print(f"\n全 {len(papers)} 件の PDF を {OUTPUT_DIR} に保存しました。")
