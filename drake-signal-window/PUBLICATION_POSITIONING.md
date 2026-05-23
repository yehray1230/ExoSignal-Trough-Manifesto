# Drake Signal Window Publication Positioning

# Drake Signal Window 發表定位

## Working Title

## 暫定標題

**Drake Signal Window: A Scenario Simulator for Temporal Selection Effects in Interstellar Radio Detection**

**德雷克訊號窗口：星際射電偵測中時間選擇效應的情境模擬器**

## Publication Identity

## 發表身份

This module should be presented as a **research-oriented interactive simulation and reproducible technical note**, not as a claim about the absolute probability of extraterrestrial civilizations.

這個模組應該被定位為**研究導向的互動模擬器與可重現技術說明**，而不是對外星文明存在機率做絕對估計。

The strongest publication framing is:

最適合的發表問題意識是：

> Given a catalog of nearby exoplanet host systems, simplified Drake-style priors, finite radio-communication lifetimes, light-travel delay, and receiver observability assumptions, what arrival-year distribution would Earth-based searches preferentially see?

> 給定鄰近系外行星宿主星目錄、簡化的德雷克式先驗、有限射電通信壽命、光速延遲與接收端可觀測性假設，地球端搜尋會偏向看見什麼樣的訊號抵達年份分布？

In other words, the project studies a detection-selection question:

換句話說，這個專案研究的是偵測選擇效應：

> If detectable radio signals exist, which timing and observability assumptions make them more or less likely to fall into Earth's receiving window?

> 如果可偵測的射電訊號存在，哪些時間與可觀測性假設會讓它們更容易或更不容易落入地球的接收窗口？

## Recommended First Release Format

## 建議的第一次發布形式

Use a staged release instead of jumping directly to a formal paper.

建議採用分階段發布，而不是直接跳到正式論文。

1. **Public project page**
   - Main entry: `drake-signal-window/index.html`
   - Audience: technically curious readers, SETI-adjacent readers, reviewers, collaborators.
   - Goal: let readers adjust assumptions and see how the reception window changes.

1. **公開專案頁**
   - 主要入口：`drake-signal-window/index.html`
   - 讀者：具技術興趣的讀者、SETI 相關讀者、審查者、潛在協作者。
   - 目標：讓讀者調整假設，直接看到接收窗口如何改變。

2. **Reproducible technical note**
   - Main entry: `drake-signal-window/README.md`
   - Supporting files: `config.json`, `simulate.py`, `outputs/*.csv`, `outputs/report.html`.
   - Goal: make the assumptions, equations, and outputs auditable.

2. **可重現技術說明**
   - 主要入口：`drake-signal-window/README.md`
   - 支援檔案：`config.json`、`simulate.py`、`outputs/*.csv`、`outputs/report.html`。
   - 目標：讓假設、方程式與輸出結果可以被檢查與重跑。

3. **Repository release**
   - Suggested tag: `v0.1-drake-signal-window`
   - Goal: freeze one coherent version of the model, data snapshot, and generated outputs.

3. **程式庫版本發布**
   - 建議 tag：`v0.1-drake-signal-window`
   - 目標：凍結一個一致的模型、資料快照與生成輸出版本。

4. **Later paper or preprint**
   - Use the release as the citable software artifact.
   - Expand the technical note into a short methods/results manuscript.

4. **後續論文或 preprint**
   - 將 release 作為可引用的軟體成果。
   - 再把 technical note 擴寫成短篇方法與結果稿。

## Core Contribution

## 核心貢獻

The module contributes a compact way to combine:

這個模組提供一個精簡方式，把以下元素組合起來：

- Drake-equation style sparse priors.
- Finite or long-tailed radio communication windows.
- Light-travel-time delay from catalog distance.
- Required effective transmit power from the existing project model.
- Receiver and search observability controls, including beam coverage, duty cycle, frequency coverage, catalog selection bias, and Breakthrough Listen epoch weighting.
- Sensitivity ranking across uncertain assumptions.

- 德雷克方程式風格的稀疏先驗。
- 有限或長尾的射電通信窗口。
- 由目錄距離導出的光行時間延遲。
- 既有專案模型中的所需有效發射功率。
- 接收端與搜尋可觀測性控制，包括波束覆蓋率、duty cycle、頻率覆蓋率、目錄選擇偏差，以及 Breakthrough Listen 觀測年代加權。
- 對不確定假設的敏感度排序。

The value is comparative and explanatory: it helps readers see which assumptions move the reception-year distribution, rather than pretending to produce a definitive SETI forecast.

它的價值在於比較與解釋：幫助讀者看見哪些假設會推動接收年份分布，而不是假裝給出決定性的 SETI 預測。

## Claims To Make

## 可以主張的內容

The publication can safely claim that the module:

這份發表可以安全地宣稱此模組：

- demonstrates temporal selection effects in Earth-based interstellar radio searches;
- turns assumptions about civilization timing and radio-window duration into arrival-year distributions;
- separates continuous all-year observability from observation-epoch-weighted scenarios;
- exposes uncertainty and sensitivity controls so readers can compare conservative and optimistic cases;
- provides reproducible CSV outputs and a standalone HTML report.

- 展示地球端星際射電搜尋中的時間選擇效應；
- 將文明時間尺度與射電窗口長度的假設轉換為訊號抵達年份分布；
- 區分全年連續可觀測情境與依觀測年代加權的情境；
- 提供不確定性與敏感度控制，讓讀者比較保守與樂觀案例；
- 提供可重現的 CSV 輸出與獨立 HTML 報告。

## Claims To Avoid

## 應避免的主張

Avoid claiming that the module:

應避免宣稱此模組：

- estimates the true number of extraterrestrial civilizations;
- predicts when Earth will receive a signal;
- proves that any listed exoplanet host is likely to contain a transmitter;
- models full radio telescope sensitivity, sky coverage, interference rejection, or signal processing in operational detail;
- represents the full Milky Way population without selection effects.

- 估計外星文明的真實數量；
- 預測地球何時會收到訊號；
- 證明任何列出的系外行星宿主星很可能含有發射源；
- 以操作細節完整模擬射電望遠鏡靈敏度、天空覆蓋、干擾排除或訊號處理；
- 在沒有選擇效應的情況下代表完整銀河系族群。

## Target Audiences

## 目標讀者

Primary:

主要讀者：

- readers interested in SETI, astrobiology, and observational selection effects;
- software reviewers evaluating whether the model is reproducible;
- collaborators who may want to improve assumptions, data, or visualization.

- 對 SETI、天體生物學與觀測選擇效應有興趣的讀者；
- 評估模型是否可重現的軟體或研究審查者；
- 可能想改善假設、資料或視覺化的協作者。

Secondary:

次要讀者：

- general science readers who can understand the idea of a finite broadcast window plus light-speed delay;
- educators looking for an interactive way to explain why detection timing matters.

- 能理解有限廣播窗口與光速延遲概念的一般科學讀者；
- 想用互動方式解釋偵測時間為何重要的教育者。

## Release Readiness Criteria

## 發布前準備條件

Before treating this as a formal public release, prepare:

在視為正式公開發布前，建議準備：

- A clean README that states scope, assumptions, run instructions, and limitations.
- A methodology section with the key equations and parameter meanings.
- A reproducibility checklist showing how to regenerate `outputs/`.
- A frozen default `config.json` for the first release.
- A generated `outputs/report.html` that matches the frozen config.
- A short results summary: peak year, probability bands, and sensitivity ranking.
- A limitations section that clearly separates model assumptions from astronomical conclusions.
- A clean git commit and release tag.

- 清楚說明範圍、假設、執行方式與限制的 README。
- 包含關鍵方程式與參數意義的方法章節。
- 說明如何重新產生 `outputs/` 的重現性清單。
- 第一次 release 專用的凍結版預設 `config.json`。
- 與凍結設定相符的 `outputs/report.html`。
- 簡短結果摘要：峰值年份、機率區間與敏感度排序。
- 清楚區分模型假設與天文結論的限制章節。
- 乾淨的 git commit 與 release tag。

## Suggested One-Paragraph Abstract

## 建議摘要

Drake Signal Window is an interactive and reproducible scenario simulator for exploring temporal selection effects in interstellar radio detection. Starting from a catalog of exoplanet host systems, it combines Drake-style sparse priors, finite radio-communication lifetimes, light-travel delay, required transmit power, and receiver observability assumptions to estimate how candidate signal arrival years would be distributed under different scenarios. The model is not intended to estimate the true abundance of extraterrestrial civilizations. Instead, it asks which timing, lifetime, power, and observation-window assumptions make potential signals more or less likely to fall inside an Earth-based search window.

Drake Signal Window 是一個互動式、可重現的情境模擬器，用來探索星際射電偵測中的時間選擇效應。它從系外行星宿主星目錄出發，結合德雷克式稀疏先驗、有限射電通信壽命、光速延遲、所需發射功率與接收端可觀測性假設，估計不同情境下候選訊號抵達年份會如何分布。此模型不旨在估計外星文明的真實豐度，而是詢問哪些時間、壽命、功率與觀測窗口假設，會讓潛在訊號更容易或更不容易落入地球端搜尋窗口。

## Recommended Next Step

## 建議下一步

The next preparation step should be a documentation pass:

下一個準備步驟應是文件整理：

- update `drake-signal-window/README.md` into a release-facing technical note;
- add a concise methodology section;
- add a reproducibility checklist;
- summarize the current default output files.

- 將 `drake-signal-window/README.md` 更新為面向 release 的技術說明；
- 補上簡潔的方法章節；
- 補上重現性清單；
- 摘要目前預設輸出檔案。
