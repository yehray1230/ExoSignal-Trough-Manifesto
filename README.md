# Observer Selection Bias in Interstellar Radio Detection

## 摘要 / Abstract

本專案以互動式 3D 視覺化與簡化天文物理模型，探討地球式射電觀測在搜尋星際文明訊號時可能產生的觀測者選擇偏誤。模型不試圖估計地外文明的真實數量，而是聚焦於一個較可檢驗的問題：在光速延遲與平方反比衰減的限制下，哪些訊號來源比較可能進入地球的可偵測樣本？

The project uses interactive 3D visualization and simplified astrophysical modeling to examine observer selection effects in Earth-based radio searches for interstellar communication. It does not estimate the absolute number of extraterrestrial civilizations. Instead, it asks which subset of possible emitters would preferentially survive the temporal and energetic filters imposed by light-speed delay and inverse-square attenuation.

## 研究問題 / Research Question

本專案的核心問題是：

> 若生命或技術文明在宇宙中廣泛分布，地球透過射電方法所能觀測到的樣本，是否仍會系統性偏向距離較近、發射功率較高，或在時間上更早具備射電能力的來源？

因此，本專案討論的是「可觀測樣本如何被物理條件篩選」，而不是直接主張「生命是否稀有」或「文明是否必然存在」。

## 專案概述 / Project Overview

前端應用程式會在 Three.js 場景中呈現系外行星與銀河星場，並估算若地球於 `2026` 年接收到某一目標訊號，該訊號的可能發射年份與所需有效射電功率。專案結合以下元素：

- 由 NASA Exoplanet Archive 查詢並整理的系外行星資料。
- 分層式銀河星圖資料，用於在前端維持星場尺度感。
- 以光年距離推導的訊號發射年代。
- 以平方反比關係估算的有效功率門檻。
- 用於比較地球射電技術史與假想訊號來源的互動式時間軸。
- 用於檢視時間門檻與能量門檻交集的 Selection Bias Lab。

## 方法 / Method

### 1. 訊號時間模型

對距離為 `d` 光年的目標，若地球於年份 `T_observed` 接收到訊號，模型將發射年份表示為：

```text
T_emit = T_observed - d
```

在目前設定中：

```text
T_observed = 2026
```

此公式表示，越遠的訊號來源必須越早具備對應射電能力，才能在 2026 年被地球接收。

### 2. 能量門檻模型

在簡化全向或等效全向發射的假設下，訊號通量會隨距離平方衰減。若接收端的最低可偵測通量門檻為 `F_min`，則所需等效全向發射功率可寫為：

```text
P_required = 4πd²F_min
```

本專案將 `4πF_min` 合併為比例常數 `K`，因此前端模型使用下式作為概念性門檻：

```text
P_required = K * d^2
```

其中 `P_required` 為所需等效全向發射功率，`d` 為距離，`K` 是以接收端偵測門檻折算而來的模型常數。現有資料產生腳本採用：

```text
P_required = 1.12e11 * distance_ly^2
```

此常數以 Five-hundred-meter Aperture Spherical radio Telescope（FAST）作為高靈敏度地球接收端的參考基準，用來代表「現代地球射電觀測可達到的高靈敏度門檻」。不過，它不應被解讀為 FAST 在所有頻寬、積分時間、訊噪比門檻與訊號型態下的完整儀器模型，而是將接收端靈敏度壓縮成單一可視化係數，用於展示距離衰減如何快速提高可偵測門檻。

在射電天文中，接收靈敏度通常以 flux density、Jansky、SEFD、頻寬與積分時間等量描述，而不是只有一個固定的「最小可接收功率」。因此，本專案中的 `1.12e11` 應理解為 FAST baseline 下的等效門檻常數，而非天文台官方靈敏度表的直接替代。

### 3. 觀測篩選模型

本專案將潛在目標依序放入三類篩選條件：

- 時間可行性：訊號來源是否必須在不合理的早期年代就具備射電能力。
- 能量可行性：假設發射功率是否足以跨越距離衰減後仍被地球偵測。
- 聯合可觀測性：同時通過時間與能量條件的目標子集合。

這些條件共同構成 SETI 射電搜尋中的「極端門檻過濾器」。

## 主要參數 / Parameters

| 參數 | 意義 | 單位 | 預設值或來源 |
|---|---|---:|---|
| `T_observed` | 地球接收訊號的年份 | year | `2026` |
| `d` | 目標距離 | light-year | 由 `sy_dist` 換算 |
| `sy_dist` | NASA 資料中的恆星距離 | parsec | NASA Exoplanet Archive |
| `distance_ly` | 換算後距離 | light-year | `sy_dist * 3.26156` |
| `T_emit` | 模型推估發射年份 | year | `T_observed - d` |
| `P_required` | 所需有效發射功率 | watt | `1.12e11 * d^2` |
| `K` | FAST baseline 等效門檻常數 | W / ly² | `1.12e11` |
| `lead_time` | 假想普通文明領先地球年數 | year | 由介面滑桿控制 |

## 視覺化介面 / Visualization

### Main Visualization

`index.html` 是主要 3D 場景。它將系外行星、星場、偵測半徑、卡爾達肖夫能量尺度與地球射電技術時間軸整合在同一個互動介面中。

主要用途：

- 觀察不同距離目標對發射年份的要求。
- 比較不同目標的所需功率等級。
- 透過偵測半徑球殼理解功率與靈敏度的影響。
- 將單一目標放入地球技術史脈絡中閱讀。

### Selection Bias Lab

`selection-bias-lab.html` 是研究面板，用於更明確地呈現篩選機制。

主要用途：

- 以距離與所需功率的相位空間檢視目標分布。
- 顯示 SETI threshold funnel 中每一層篩選後的剩餘樣本。
- 觀察「普通文明只領先地球數十年至數百年」時，可觀測樣本如何急遽縮小。
- 將可觀測樣本理解為被物理限制塑形後的非代表性子集合。

## 資料來源與再現性 / Data and Reproducibility

系外行星資料由 `fetch_exoplanets.py` 透過 NASA Exoplanet Archive TAP API 查詢：

```text
https://exoplanetarchive.ipac.caltech.edu/TAP/sync
```

目前查詢欄位包含：

- `pl_name`
- `hostname`
- `sy_dist`

星圖資料採分層策略：

- `data/stars-core.json`：少量明亮實星錨點。
- `data/stars-lod/lod1.json`：程序生成的第一層銀河點雲。
- runtime procedural stars：執行時產生的遠場星點，用於增加尺度感。

資料策略的細節請見 [data/README.md](data/README.md)。

## 接收端基準 / Receiver Baseline

本專案選用 FAST 作為接收端靈敏度基準，是因為 FAST 是目前極具代表性的高靈敏度單口徑射電望遠鏡。這個選擇的目的，是讓模型中的能量門檻接近「地球現有高階射電觀測能力」的量級，而不是任意設定一個抽象門檻。

需要注意的是，FAST 的實際偵測能力會依觀測頻段、接收機、系統溫度、頻寬、積分時間、訊號漂移率、偏振處理與搜尋管線而變動。為了維持互動模型簡潔，本專案將這些儀器因素折算為單一比例常數 `K`。因此，畫面上的 `P_required` 應解讀為「在 FAST baseline 偵測門檻下所需的等效全向發射功率」，而不是對特定 FAST 觀測設定的精確預報。

相關背景：

- NASA Exoplanet Archive 將 `sy_dist` 定義為系統距離，單位為 parsec。
- NRAO 說明射電天文常以 flux density 與 Jansky 表示接收訊號強度。
- FAST 相關文獻通常以系統溫度、增益、SEFD 或特定 SETI 搜尋的 EIRP 門檻描述靈敏度。

## 模型限制 / Limitations

本專案目前採用概念性模型，並不包含完整射電天文儀器模擬。以下因素尚未細緻納入：

- 星際介質造成的閃爍、吸收或散射。
- 頻寬、訊號編碼、調變方式與搜尋策略完整性。
- 都卜勒漂移與觀測窗口限制。
- 發射占空比與文明主動發射意圖。
- 定向波束幾何的詳細建模。
- 行星適居性、生命發生率或文明壽命的統計模型。
- FAST 在特定接收機、頻寬、積分時間與搜尋管線下的完整 radiometer equation 校準。

因此，圖中門檻應被視為「物理選擇壓力的方向性示範」，而不是對任一特定目標的觀測預報。

## 專案結構 / Repository Structure

```text
.
|-- index.html                  # Main Three.js visualization
|-- selection-bias-lab.html     # Research dashboard for detection-selection effects
|-- ASSUMPTIONS.md              # Modeling assumptions and interpretation notes
|-- data.js                     # Exoplanet dataset used by the app
|-- fetch_exoplanets.py         # NASA Exoplanet Archive data fetcher
|-- data/
|   |-- README.md               # Star catalog data and reproducibility notes
|   |-- stars-core.json         # Compact real-star anchor layer
|   `-- stars-lod/
|       `-- lod1.json           # First LOD starfield layer
`-- scripts/
    `-- build_star_catalog.py   # Star catalog layer generator
```

## 本機執行 / Running Locally

由於前端會透過 `fetch` 載入 JSON 星表資料，建議使用本機靜態伺服器啟動，而不是直接雙擊開啟 `index.html`。

```bash
python -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/index.html
```

若 Python 不在 `PATH` 中，也可使用任何能提供專案根目錄的靜態檔案伺服器。

## 重新產生資料 / Regenerating Data

Fetch or refresh the exoplanet data:

```bash
python fetch_exoplanets.py
```

Regenerate the compact star catalog layers:

```bash
python scripts/build_star_catalog.py
```

大型原始星表不應直接提交至 Git。建議放置於 Git 忽略路徑，例如 `data/raw/`，或在發佈時透過 GitHub Release、物件儲存或 CDN 提供。

## 解讀結論 / Interpretation

本專案的主要結論是條件式的：若生命或文明廣泛分布，而地球透過受光速延遲與平方反比衰減限制的射電方法搜尋，則可觀測樣本仍可能高度不代表底層真實分布。

換言之，未偵測到普通文明不必然代表普通文明稀少；它也可能表示普通文明在進入可觀測樣本之前，就已被時間與能量條件排除。地球在此框架下呈現出的「技術窪地」，是觀測方法與物理限制共同塑造的結果。
