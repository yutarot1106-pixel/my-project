# 除外リスト（短距離ユース版・母集団の絞り込み）

## 除外基準（閾値の定義）

| 基準 | 内容 | 根拠 |
|---|---|---|
| (a) レンジ超過 | カタログ最大測距 **>120m**（要求レンジ40mの3倍超）の機種・グレード | 「40〜50mを大きく超える」を機械的に判定できる閾値として3倍(=120m)を採用。長距離グレードは光学系/アンテナ/価格が長距離要件に最適化されており、30–40m用途では過剰スペック＝コスト・サイズのノイズになる |
| (b) 長距離グレード名目 | メーカー自身が長距離用（LRR/長距離イメージング/車載長距離LiDAR）と位置付けるもの | (a)と実質同義の補助基準 |
| (c) 入手性 | 生産終了・車両一体で単体入手不可 | 実選定の母集団として不適切 |

境界の扱い: **120mちょうど・以下は残す**（例: Ouster OS1=120m@10%はメーカー区分が「mid-range」、TI単チップの~100–120mはアンテナ設計依存で短距離構成が可能なため継続）。

## 除外した機種（26件）

| センサー | 機種 | カタログ最大 | 除外理由 |
|---|---|---|---|
| ステレオ | SUBARU EyeSight ver.3（基線35cm） | 110m | 長基線車載・車両一体で単体入手不可 (b)(c) |
| ミリ波 | TI AWR2944 | ~200m | イメージング設計向け (a) |
| ミリ波 | TI AWR2243カスケード4chip | ~350m | 長距離リファレンス設計 (a) |
| ミリ波 | Continental ARS408-21 | 250m | 長距離グレード (a)(b) |
| ミリ波 | Continental ARS540 | 300m | 4D長距離 (a)(b) |
| ミリ波 | Bosch Front Radar FR5 | 210m | 長距離 (a) |
| ミリ波 | Bosch LRR4 | 250m | 長距離 (a)(b) |
| ミリ波 | Aptiv ESR 2.5 | 174m | 長距離 (a) |
| ミリ波 | ZF FRGen21 | 350m | 長距離 (a) |
| ミリ波 | Arbe Phoenix | 300m | 長距離 (a) |
| ミリ波 | Oculii Eagle | 350m | 長距離 (a) |
| ミリ波 | Navtech CTS350-X | 250m | 長距離・インフラ用 (a) |
| ミリ波 | Uhnder S80 | 300m | 長距離 (a) |
| LiDAR | Benewake TF03-180 | 180m | 長距離1D (a) |
| LiDAR | Velodyne HDL-32E | 100m | 生産終了 (c) |
| LiDAR | Velodyne HDL-64E | 120m | 生産終了・13kg大型 (c) |
| LiDAR | Velodyne VLS-128 Alpha Prime | 245m | 車載長距離 (a)(b) |
| LiDAR | Ouster OS2-128 | 210m | 長距離 (a)(b) |
| LiDAR | Hesai AT128 | 200m | 車載長距離 (a)(b) |
| LiDAR | RoboSense RS-LiDAR-M1 | 150m | 車載長距離 (a)(b) |
| LiDAR | RoboSense Helios-16 | 150m | カタログ150m>120m (a) |
| LiDAR | Livox Avia | 190m(10%) | 長距離 (a) |
| LiDAR | Luminar Iris | 250m | 車載長距離 (a)(b) |
| LiDAR | Innoviz InnovizOne | 250m | 車載長距離 (a)(b) |
| LiDAR | Valeo SCALA Gen2 | 200m | 車載長距離 (a)(b) |
| LiDAR | Aeva Aeries II | 400m | 長距離FMCW (a) |

## LiDARの方式フィルタ（3D方式のみに限定）

本比較の趣旨（30〜40m先の対象の**面的な形状・方位の取得**）に照らし、**LiDARは3D方式のみを対象**とする。以下は方式を理由に除外:

- **1D単点型（5機除外）**: Benewake TF-Luna / TFmini-S / TF02-Pro、Garmin LIDAR-Lite v3 / v4 LED — 固定1方向の距離のみで方位・形状を持たない。40mに届く機（TF02-Pro・LIDAR-Lite v3）も本用途では役割が別（定点測距・高度計）。
- **2D走査型（11機除外）**: SLAMTEC RPLIDAR A1/S2/A3、北陽 URG-04LX / UST-10LX / UST-20LX / UTM-30LX、SICK TiM571 / LMS111、YDLIDAR TG30、LDROBOT LD19 — 単一平面のみで高さ方向の形状を取得できない。かつ本母集団の2D機は全機カタログ最大30m以下で40m要件にも届かない。

## 補充した機種

**当初補充（16件・同グレード帯: 短〜中距離）**
- LiDAR（+10）: 上記の通り3D方式フィルタで全て除外
- ミリ波（+6）: TI IWR6843AOP、Ainstein US-D1、Nanoradar SP25、InnoSenT iSYS-4004、RFbeam K-MD2、smartmicro DRVEGRD 152

**3D限定に伴う近〜中距離3D LiDARの追補（+12件・全て≤120m）**
RoboSense Bpearl（30m近距離ドーム）／Hesai QT128（50m）・QT64（60m）・PandarXT-16（120m）／Velodyne Puck LITE・Puck Hi-Res（100m）／Ouster OS1-32・OS1-64・OS0-32・OS0-64／Livox Mid-70（90m）／Unitree 4D LiDAR L2

補充後の母集団: **超音波24／ステレオ22／ミリ波15／LiDAR 20（3Dのみ・計81機種）**。ミリ波のみn=20未達（→注記で申告）。LiDARは3D限定でn=20を確保。
