# Star Catalog Data and Reproducibility Notes

本目錄保存前端可直接載入的精簡星圖資料。專案刻意不提交大型原始星表，以避免儲存庫體積膨脹，並讓 GitHub 頁面與本機靜態伺服器都能穩定載入。

## 檔案說明 / Files

| 檔案 | 內容 | 性質 |
|---|---|---|
| `stars-core.json` | 少量明亮命名恆星 | 手動整理的真實星體錨點 |
| `stars-lod/lod1.json` | 第一層銀河點雲 | 由腳本生成的視覺化資料 |

## 資料策略 / Data Strategy

本專案採用分層式星圖策略：

- 使用少量明亮實星作為可辨識的天文錨點。
- 使用程序生成的 LOD 點雲呈現銀河尺度密度。
- 在前端執行時補充遠場星點，以增加場景深度。
- 將大型 Gaia、HYG、FITS、CSV 或壓縮原始資料排除在 Git 之外。

這種做法犧牲完整星表精度，換取前端效能、儲存庫可攜性與 GitHub 顯示穩定性。

## 再現方式 / Regeneration

重新產生精簡星圖資料：

```bash
python scripts/build_star_catalog.py
```

腳本會輸出：

```text
data/stars-core.json
data/stars-lod/lod1.json
```

## 大型星表建議 / Large Catalog Policy

若未來整合 Gaia、HYG 或其他大型星表，建議採用以下流程：

1. 將原始資料放置於 Git 忽略路徑，例如 `data/raw/`。
2. 以離線腳本轉換成前端可載入的分塊 LOD 檔案。
3. 將大型輸出放在 GitHub Release、物件儲存或 CDN。
4. 在文件中記錄資料版本、查詢條件、轉換腳本與產生日期。

## 解讀限制 / Interpretation Limits

目前星圖層主要用於建立視覺尺度與空間脈絡，不應被視為完整天體測量資料庫。若研究問題需要精確星體位置、亮度、光譜型或選樣函數，應回到原始天文資料庫並建立可追溯的資料處理流程。
