# Drake Signal Window Simulation

# Drake Signal Window 模擬器

Drake Signal Window 是一個研究導向的互動模擬器與可重現技術說明模組。它使用專案既有的 `data.js` 系外行星目標、距離與所需功率估計，加入德雷克方程式風格的稀疏先驗、有限射電通信窗口、光速延遲與觀測可見性假設，用來探索地球端可能接收到星際射電訊號的年份分布。

It uses the project's existing `data.js` exoplanet targets, distances, and required-power estimates, then adds Drake-style sparse priors, light-travel delay, and observability assumptions to explore the possible arrival-year distribution of interstellar radio signals at Earth. Finite radio-communication windows are retained as a synchronization-loss hypothesis rather than the primary filter.

它的核心問題不是「外星文明有多少」，而是：

Its core question is not "how many extraterrestrial civilizations exist", but:

> 在一組明確假設下，哪些訊號比較可能穿過時間、功率與觀測窗口的篩選，落入地球可接收的年份範圍？

> Under a clear set of assumptions, what would Earth observe if communicative civilizations remain radio-visible, and how much additional loss is introduced by finite-window synchronization?

## Publication Positioning / 發表定位

This module is being prepared as a research-oriented interactive simulation and reproducible technical note. Its strongest framing is not "how many extraterrestrial civilizations exist", but:

這個模組正在被整理為研究導向的互動模擬器與可重現技術說明。它最適合的定位不是「外星文明有多少」，而是：

> Given simplified Drake-style priors, continuous-emission observability, light-travel delay, and a separate finite-window synchronization hypothesis, what arrival-year distribution would Earth-based searches preferentially see?

> 給定簡化的德雷克式先驗、有限射電通信壽命、光速延遲與可觀測性假設，地球端搜尋會偏向看見什麼樣的訊號抵達年份分布？

See `PUBLICATION_POSITIONING.md` for the release framing, safe claims, claims to avoid, target audiences, and readiness checklist.

更多 release 定位、安全可主張內容、應避免主張、目標讀者與準備清單，請見 `PUBLICATION_POSITIONING.md`。

## Abstract / 摘要

Drake Signal Window explores temporal selection effects in interstellar radio detection. Starting from a catalog of exoplanet host systems, it combines Drake-style sparse priors, continuous-emission observability, light-travel delay, required transmit power, and receiver observability assumptions to estimate how candidate signal arrival years would be distributed under different scenarios. Finite radio-communication lifetimes remain available as a second-layer synchronization-loss hypothesis. The model is not intended to estimate the true abundance of extraterrestrial civilizations.

Drake Signal Window 探索星際射電偵測中的時間選擇效應。它從系外行星宿主星目錄出發，結合德雷克式稀疏先驗、有限射電通信壽命、光速延遲、所需發射功率與接收端可觀測性假設，估計不同情境下候選訊號抵達年份會如何分布。此模型不旨在估計外星文明的真實豐度，而是詢問哪些時間、壽命、功率與觀測窗口假設，會讓潛在訊號更容易或更不容易落入地球端搜尋窗口。

## Files / 檔案

- `index.html`: interactive front end for adjusting assumptions and redrawing the scenario charts.
- `index.html`：可互動前端，用於調整假設並重新繪製情境圖表。
- `config.json`: default release configuration for the simulation.
- `config.json`：模擬器的預設 release 設定。
- `simulate.py`: standard-library-only Python simulator that reads `../data.js` and writes CSV plus a standalone HTML report.
- `simulate.py`：只使用 Python 標準函式庫的模擬腳本，讀取 `../data.js` 後輸出 CSV 與獨立 HTML 報告。
- `PUBLICATION_POSITIONING.md`: release framing, safe claims, claims to avoid, target audiences, and readiness checklist.
- `PUBLICATION_POSITIONING.md`：release 定位、安全可主張內容、應避免主張、目標讀者與準備清單。
- `outputs/arrival_probability_by_year.csv`: baseline annual probability that Earth receives at least one detectable signal, plus finite-window synchronization-loss columns.
- `outputs/arrival_probability_by_year.csv`：地球每年接收到至少一個可偵測訊號的 baseline 機率。
- `outputs/monte_carlo_probability_bands.csv`: uncertainty bands from Monte Carlo variation of model assumptions.
- `outputs/monte_carlo_probability_bands.csv`：由 Monte Carlo 假設變動產生的不確定性區間。
- `outputs/monte_carlo_samples.csv`: sampled parameter runs used to produce probability bands.
- `outputs/monte_carlo_samples.csv`：用來產生機率區間的抽樣參數組。
- `outputs/selected_timing_arrival_year_distribution.csv`: arrival-year density for the selected timing model.
- `outputs/selected_timing_arrival_year_distribution.csv`：所選時間模型下的抵達年份密度。
- `outputs/sensitivity_ranking.csv`: ranked assumptions by impact on peak probability or peak year.
- `outputs/sensitivity_ranking.csv`：依峰值機率或峰值年份影響排序的假設敏感度。
- `outputs/report.html`: standalone browser report generated from the current outputs.
- `outputs/report.html`：由目前輸出生成、可直接在瀏覽器開啟的獨立報告。

## Method Summary / 方法摘要

For a target at distance `d` light-years, if a civilization enters radio communication at `T_start` and remains radio-visible for `L` years, Earth can receive that signal in the interval:

對距離 `d` 光年的目標，如果某文明在 `T_start` 進入射電通信階段，並維持 `L` 年的射電可見期，則地球可能接收該訊號的時間區間為：

```text
T_start + d <= T_receive <= T_start + L + d
```

The simulator estimates `T_start` from two configurable timing assumptions:

模擬器用兩個可設定的時間假設估計 `T_start`：

```text
T_start = birth_year + development_duration
```

The Drake-style sparse prior is built from:

德雷克式稀疏先驗由下列項目組成：

```text
R_star * fp * ne * fl * fi * fc * L
```

where `L` is the reference radio-window lifetime. The result is spread across the catalog as a bounded per-target prior, because this catalog is a search sample rather than the full Milky Way population.

其中 `L` 是參考射電窗口壽命。由於此目錄是搜尋樣本，而不是完整銀河系族群，結果會被分配到目錄目標上，形成有上限的 per-target prior。

Detectability is weighted by the required effective transmit power already present in `../data.js`. Instead of a hard cutoff, the simulator uses a smooth falloff controlled by:

可偵測性由 `../data.js` 中既有的所需有效發射功率加權。模擬器不使用硬切斷，而是用以下參數控制平滑衰減：

```text
max_effective_transmit_power_w
power_rolloff_decades
```

Receiver and survey observability are then applied through:

接收端與搜尋可觀測性接著透過下列項目套用：

```text
beam_coverage * duty_cycle * frequency_coverage
```

Additional rigor controls can down-weight catalog selection effects, broaden uncertainty bands, and penalize strongly optimistic combinations of lifetime, power, and observability assumptions.

額外的 rigor controls 可以降低目錄選擇效應的權重、擴大不確定性區間，並對過度樂觀的壽命、功率與可觀測性假設組合加入懲罰。

## Default Configuration / 預設設定

The current default scenario in `config.json` uses:

目前 `config.json` 的預設情境使用：

- Observation range: `1800` to `7000`, sampled every `10` years.
- 觀測年份範圍：`1800` 到 `7000`，每 `10` 年取樣。
- Observation epoch model: `continuous`.
- 觀測年代模型：`continuous`。
- Catalog target cap: `800`.
- 目錄目標上限：`800`。
- Monte Carlo uncertainty: enabled, with `50` sampled scenarios.
- Monte Carlo 不確定性：啟用，含 `50` 組抽樣情境。
- Drake terms: `fp = 0.9`, `ne = 0.2`, `fl = 0.25`, `fi = 0.08`, `fc = 0.2`.
- Drake 參數：`fp = 0.9`、`ne = 0.2`、`fl = 0.25`、`fi = 0.08`、`fc = 0.2`。
- Timing model: lognormal.
- 時間模型：lognormal。
- Radio-window model: infinite for the primary observability layer; finite windows are reported as synchronization loss.
- 射電窗口模型：主層使用 infinite；有限窗口作為同步損失假說輸出。
- Reference radio-window lifetime for the synchronization hypothesis: `650` years.
- 參考射電窗口壽命：`650` 年。
- Maximum effective transmit power: `1.0e18 W`.
- 最大有效發射功率：`1.0e18 W`。
- Beam coverage: `0.35`.
- 波束覆蓋率：`0.35`。
- Duty cycle: `0.5`.
- Duty cycle：`0.5`。
- Frequency coverage: `0.45`.
- 頻率覆蓋率：`0.45`。
- Catalog selection bias strength: `0.4`.
- 目錄選擇偏差強度：`0.4`。
- Assumption correlation penalty: `0.25`.
- 假設相關性懲罰：`0.25`。

## Current Output Summary / 目前輸出摘要

The current generated outputs indicate a broad, still-rising reception curve through the extended 20,000 CE simulation horizon rather than a sharp prediction.

目前生成的輸出顯示的是寬廣的 baseline 接收窗口，而不是尖銳的預測。

- Baseline annual probability peaks near year `3400`.
- Baseline 年度機率峰值約在 `3400` 年。
- At the baseline peak, `probability_at_least_one_signal` is approximately `0.00623`.
- 在 baseline 峰值處，`probability_at_least_one_signal` 約為 `0.00623`。
- The baseline peak has a local 5%-95% uncertainty band of roughly `0.00426` to `0.00906`.
- Baseline 峰值附近的局部 5%-95% 不確定性區間約為 `0.00426` 到 `0.00906`。
- Monte Carlo median probability peaks near year `3500`, with `probability_p50` approximately `0.00671`.
- Monte Carlo 中位數機率峰值約在 `3500` 年，`probability_p50` 約為 `0.00671`。
- In the wider Monte Carlo band near the median peak, `probability_p05` is approximately `0.00091` and `probability_p95` is approximately `0.04488`.
- 在中位數峰值附近較寬的 Monte Carlo 區間中，`probability_p05` 約為 `0.00091`，`probability_p95` 約為 `0.04488`。
- The selected timing arrival-year density peaks around year-bin `3025`.
- 所選時間模型的抵達年份密度峰值約在 year-bin `3025`。
- The most influential assumptions in the current sensitivity ranking are `Intelligence fraction`, `Transmit power`, and `Communicative fraction`.
- 目前敏感度排序中影響最大的假設是 `Intelligence fraction`、`Transmit power` 與 `Communicative fraction`。

These values describe the current default configuration only. They should be treated as scenario outputs, not empirical predictions.

這些數值只描述目前預設設定。它們應被視為情境輸出，而不是經驗性預測。

## Run / 執行方式

From the repository root, run:

從 repository 根目錄執行：

```powershell
python .\drake-signal-window\simulate.py
```

In the Codex desktop environment, the bundled Python can be used:

在 Codex 桌面環境中，也可以使用內建 Python：

```powershell
& "C:\Users\yehra\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\drake-signal-window\simulate.py
```

The script writes regenerated files into `drake-signal-window/outputs/`.

腳本會把重新生成的檔案寫入 `drake-signal-window/outputs/`。

## Reproducibility Checklist / 重現性清單

Use this sequence when preparing a release snapshot:

準備 release snapshot 時，建議使用以下順序：

1. Refresh or confirm the exoplanet and derived target data:

1. 更新或確認系外行星與衍生目標資料：

```powershell
python .\fetch_exoplanets.py
```

2. Refresh or confirm Breakthrough Listen observation matches, if that dataset is part of the release:

2. 如果 release 包含 Breakthrough Listen 資料，更新或確認觀測匹配：

```powershell
python .\scripts\fetch_breakthrough_listen.py
```

3. Regenerate the star catalog layers used by the broader project visualization:

3. 重新生成主專案視覺化使用的星表 layers：

```powershell
python .\scripts\build_star_catalog.py
```

4. Regenerate the Drake Signal Window outputs:

4. 重新生成 Drake Signal Window 輸出：

```powershell
python .\drake-signal-window\simulate.py
```

5. Confirm these generated outputs exist:

5. 確認下列生成輸出存在：

```text
drake-signal-window/outputs/arrival_probability_by_year.csv
drake-signal-window/outputs/monte_carlo_probability_bands.csv
drake-signal-window/outputs/monte_carlo_samples.csv
drake-signal-window/outputs/selected_timing_arrival_year_distribution.csv
drake-signal-window/outputs/sensitivity_ranking.csv
drake-signal-window/outputs/report.html
```

6. Record the release configuration from:

6. 記錄 release 使用的設定檔：

```text
drake-signal-window/config.json
```

## Radio Window Modes / 射電窗口模式

`radio_window_model` can be set to `fixed`, `lognormal`, or `infinite`.

`radio_window_model` 可設定為 `fixed`、`lognormal` 或 `infinite`。

The primary probability layer now assumes continuous radio visibility after a civilization becomes communicative. Non-infinite radio-window modes are still evaluated as a second layer and reported as synchronization loss.

主機率層現在假設文明進入可通信階段後持續可見；非 infinite 的射電窗口模式仍會作為第二層同步損失進行評估。

- `fixed`: every communicative civilization has the same finite broadcast duration.
- `fixed`：每個可通信文明都有相同的有限廣播時間。
- `lognormal`: the slider/config value is the approximate mean, with many short windows and a few very long windows.
- `lognormal`：slider/config 值代表近似平均值，會產生許多短窗口與少數很長的窗口。
- `infinite`: once a civilization becomes radio-communicative, the simulator does not apply a shutdown time. The `radio_window_years` value is still used as the reference lifetime for the sparse Drake prior, so this option does not create an infinite Drake weight.
- `infinite`：文明一旦進入射電通信階段，模擬器不套用關閉時間。`radio_window_years` 仍會作為稀疏 Drake prior 的參考壽命，因此此選項不會產生無限大的 Drake 權重。

## Rigor Controls / 嚴謹性控制

The interactive page and `simulate.py` include additional uncertainty and observability controls.

互動頁與 `simulate.py` 包含額外的不確定性與可觀測性控制。

- `uncertainty_spread`: varies `fl`, `fi`, `fc`, and the reference radio lifetime to output 5%-95% probability bands.
- `uncertainty_spread`：改變 `fl`、`fi`、`fc` 與參考射電壽命，以輸出 5%-95% 機率區間。
- `catalog_selection_bias`: down-weights distant or less complete catalog entries instead of treating the target list as an unbiased sample.
- `catalog_selection_bias`：降低遙遠或不完整目錄項目的權重，避免把目標清單視為無偏樣本。
- `beam_coverage`, `duty_cycle`, and `frequency_coverage`: model whether a transmitter points toward Earth, is active at the receiving time, and overlaps the searched frequency band.
- `beam_coverage`、`duty_cycle`、`frequency_coverage`：模擬發射源是否指向地球、在接收時間是否啟用，以及是否落在搜尋頻段。
- `assumption_correlation`: adds a conservative penalty so long lifetime, high power, and observability assumptions are not treated as fully independent.
- `assumption_correlation`：加入保守懲罰，避免長壽命、高功率與高可觀測性假設被視為完全獨立。
- `observation_epoch_model`: set to `continuous` for the original all-years scenario, or `breakthrough_listen` to weight reception probability around matched Breakthrough Listen observation years from `../data.js`.
- `observation_epoch_model`：可設為 `continuous` 代表原始全年情境，或設為 `breakthrough_listen` 以 `../data.js` 中匹配到的 Breakthrough Listen 觀測年份附近加權接收機率。
- `bl_observation_window_years`: Gaussian smoothing width, in years, used when `observation_epoch_model` is `breakthrough_listen`.
- `bl_observation_window_years`：當 `observation_epoch_model` 為 `breakthrough_listen` 時使用的 Gaussian smoothing 寬度，單位為年。
- `outputs/sensitivity_ranking.csv`: ranks which assumptions most change peak reception probability or peak receive year.
- `outputs/sensitivity_ranking.csv`：排序哪些假設最會改變峰值接收機率或峰值接收年份。

## Interpretation / 解讀

This is a conditional scenario model. A high value in the output means that a particular combination of assumptions makes reception in that year more favored relative to other years in the same scenario. It does not mean that a signal is likely in an absolute operational sense.

這是一個條件式情境模型。輸出中的高值表示在同一情境內，某組假設讓該年份相對於其他年份更有利於接收；它不表示在實際操作意義上訊號必然很可能出現。

The main use of the model is comparative:

此模型的主要用途是比較：

- Compare short, long, lognormal, and infinite radio-window assumptions.
- 比較短、長、lognormal 與 infinite 射電窗口假設。
- Compare continuous observability against observation-epoch weighting.
- 比較連續可觀測性與觀測年代加權。
- Identify which uncertain assumptions move the reception-year distribution the most.
- 找出哪些不確定假設最會推動接收年份分布。
- Communicate why timing and light-travel delay matter for Earth-based SETI searches.
- 說明為什麼時間尺度與光行延遲對地球端 SETI 搜尋很重要。

## Limitations / 限制

- The model does not estimate the true number of extraterrestrial civilizations.
- 此模型不估計外星文明的真實數量。
- The catalog is not treated as a complete or unbiased sample of the Milky Way.
- 此目錄不被視為完整或無偏的銀河系樣本。
- Radio telescope sensitivity, interference rejection, sky coverage, cadence, and signal processing are simplified into high-level observability controls.
- 射電望遠鏡靈敏度、干擾排除、天空覆蓋、觀測 cadence 與訊號處理都被簡化為高層級可觀測性控制。
- `required_power_w` is inherited from the broader project model and should be interpreted as an effective scenario threshold, not a full instrument pipeline.
- `required_power_w` 繼承自主專案模型，應解讀為有效情境門檻，而不是完整儀器流程。
- Drake parameters are exploratory assumptions, not measured constants.
- Drake 參數是探索性假設，不是已量測常數。
- The outputs are sensitive to intelligence fraction, communicative fraction, transmitter power, observability assumptions, and the finite-window synchronization hypothesis.
- 輸出對智慧比例、可通信比例、發射功率、可觀測性假設與有限窗口同步假說敏感。
- The default scenario is a release baseline for comparison, not a preferred scientific conclusion.
- 預設情境是用於比較的 release baseline，不是首選科學結論。

## Recommended Citation Framing / 建議引用方式

When referring to this module in text, describe it as:

在文字中引用此模組時，建議描述為：

> A reproducible scenario simulator for temporal and observational selection effects in interstellar radio signal detection.

> 一個用於探索星際射電訊號偵測中時間與觀測選擇效應的可重現情境模擬器。

Avoid describing it as a predictor of alien civilizations or a forecast of first contact.

避免把它描述成外星文明預測器，或首次接觸時間預測。
