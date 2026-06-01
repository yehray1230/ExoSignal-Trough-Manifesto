# Model Limitations and Non-Claims / 模型限制與非宣稱事項

本文件詳細界定「觀測者選擇偏誤（Observer Selection Bias）」視覺化模型與計算框架的物理與數據限制。

---

## 1. Physical & Signal Simplifications / 物理與訊號簡化

### 1.1 Vacuum Propagation Assumption / 真空傳播假設
* **Limitation**: The calculations assume radio signals propagate through a perfect vacuum, adhering strictly to the inverse-square law ($P \propto d^2$).
* **Reality**: In the interstellar medium (ISM), signals experience dispersion, scattering, and scintillation caused by free electrons and interstellar dust. These effects can significantly degrade, smear, or modulate the signal strength and structure at the receiver.
* **中文說明**: 模型假設訊號在完美真空中傳播，嚴格遵循平方反比定律。在實際星際介質（ISM）中，自由電子與星際塵埃會導致色散、散射與閃爍，這可能會大幅降低、拉寬或調變抵達接收端的訊號強度與結構。

### 1.2 Equivalent Isotropic Radiated Power (EIRP) vs. Directed Beaming / 等效全向輻射功率與定向波束
* **Limitation**: The model uses EIRP (Equivalent Isotropic Radiated Power) as the baseline for required power. 
* **Reality**: If an emitter uses high-gain directional antennas (e.g., planetary radar or phased arrays) rather than broadcasting isotropically, the actual transmitter power required to achieve detection could be several orders of magnitude lower. However, this introduces a geometric duty-cycle constraint (the beam must be precisely aligned with Earth), which is not currently modeled in the 3D visualization.
* **中文說明**: 模型以等效全向輻射功率（EIRP）作為計算基準。若發射源使用高增益定向天線（如行星雷達或相位陣列）而非各向同性廣播，其被偵測所需的實際物理發射功率將下降數個數量級，但代價是引入極低的天線對準機率（幾何占空比），本模型尚未對定向波束進行幾何與對準機率建模。

### 1.3 Modulation, Bandwidth, and Drift Rate / 調變、頻寬與漂移率
* **Limitation**: The simplified threshold constant $K = 1.12 \times 10^{11} \text{ W/ly}^2$ assumes a typical narrow-band carrier signal.
* **Reality**: Real SETI searches must account for signal modulation, bandwidth, polarization, and Doppler drift rates due to orbital motions of both the emitter and Earth. Broad-band or highly drifted signals would require different energy thresholds and integration times.
* **中文說明**: 本專案簡化的門檻常數 $K$ 假設訊號為典型的窄頻載波。實際的 SETI 搜尋必須考慮發射端與地球公轉與自轉產生的都卜勒漂移、訊號調變、頻寬與偏振。寬頻訊號或高漂移率訊號在接收端將需要完全不同的能量門檻與積分時間。

---

## 2. Catalog & Observational Biases / 星表與觀測偏誤

### 2.1 Exoplanet Archive Incompleteness / 系外行星星表的不完整性
* **Limitation**: The visualization displays only known, confirmed exoplanets from the NASA Exoplanet Archive.
* **Reality**: Our current exoplanet catalogs are heavily affected by selection effects (biases toward massive planets close to bright stars, detected via transit or radial velocity). The stellar systems rendered do not represent the isotropic, unbiased distribution of all stars in the Milky Way, nor do they define the absolute boundaries of where life could exist.
* **中文說明**: 網頁視覺化僅顯示 NASA Exoplanet Archive 中已證實的系外行星。現有的行星星表本身存在嚴重的觀測選擇效應（偏向距離近、質量大、利用凌日法或視向速度法易於偵測的系統），圖中的分布並不代表銀河系恆星與行星的真實空間分布，亦非適居生命的絕對邊界。

### 2.2 Breakthrough Listen Target Matching / Breakthrough Listen 觀測匹配限制
* **Limitation**: The spatial matching radius of $0.2^\circ$ is a geometric filter ensuring the exoplanetary system falls within the half-power beam width (HPBW) of a typical single-dish telescope (like GBT or Parkes) at L-band.
* **Reality**: A spatial match does not imply that Breakthrough Listen has actively observed, scheduled, or analyzed signals from that specific system across all frequencies, nor does it guarantee the target was observed during active emitter broadcast windows.
* **中文說明**: 星表匹配所採用的 $0.2^\circ$ 夾角僅為幾何過濾器，用以確保該系外行星位於單口徑望遠鏡（如 GBT 或 Parkes）在 L 頻段的半功率波束寬度（HPBW）內。空間上的匹配不代表 Breakthrough Listen 已對該特定系統進行了所有頻段的實際觀測或排程，亦無法保證觀測時間與假想發射源的廣播窗口重疊。

---

## 3. Non-Claims / 非宣稱事項聲明

為了確保科學推論的嚴謹性，本專案**明確聲明不主張**以下事項：

1. **No Astrobiological Confirmation**: This project does not claim that extraterrestrial life or technological civilizations exist on any of the target exoplanets.
   * **無天文生物學證實**：本專案不主張或證實任何特定系外行星上確實存在地外生命或技術文明。
2. **No Drake Equation Solution**: The visualization models the *observational filters* of electromagnetic search methods. It does not attempt to solve the Drake Equation or estimate the absolute number ($N$) of active civilizations in the galaxy.
   * **非德雷克方程式解**：本模型旨在探討電磁偵測方法的「觀測過濾效應」，無意解出德雷克方程式或估算銀河系中文明的絕對數量。
3. **No Alternative Communication Exclusion**: We do not claim that radio is the primary or optimal medium for interstellar communication. Civilizations may utilize lasers (Optical SETI), neutrinos, gravitational waves, or physics yet unknown to human science.
   * **不排除其他通訊手段**：本專案不宣稱無線電是星際通訊的主流或最佳媒介；文明可能使用雷射（光學 SETI）、中微子、引力波或人類科學尚未掌握的物理機制通訊。
4. **No Official Observatory Simulation**: The constants used to derive the "FAST Baseline" are intended for conceptual illustration of physical constraints. They do not represent the official sensitivity charts, operational configurations, or receiver limits of the Five-hundred-meter Aperture Spherical radio Telescope (FAST).
   * **非官方望遠鏡精確模擬**：本專案所推導的「FAST 接收端基準」僅用於展示物理尺度的限制，不代表 FAST 官方的實際接收機靈敏度曲線、觀測排程或特定科學管線的極限。
