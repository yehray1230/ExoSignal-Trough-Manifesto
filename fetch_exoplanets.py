import requests
import pandas as pd
import io

def fetch_exoplanet_data():
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    # 使用 ADQL (Astronomical Data Query Language) 查詢
    query = """
    SELECT TOP 2000 pl_name, hostname, sy_dist 
    FROM pscomppars 
    WHERE sy_dist IS NOT NULL 
    ORDER BY sy_dist ASC
    """
    
    params = {
        "query": query,
        "format": "csv"
    }
    
    print("Fetching data from NASA Exoplanet Archive API...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    # 使用 pandas 讀取 CSV 資料
    df = pd.read_csv(io.StringIO(response.text))
    
    # 進行資料轉換與新增推算欄位
    # sy_dist (秒差距) 轉換為 distance_ly (光年)
    df['distance_ly'] = df['sy_dist'] * 3.26156
    
    # signal_year = 2026 - distance_ly
    df['signal_year'] = 2026 - df['distance_ly']
    
    # Conceptual FAST-baseline EIRP threshold:
    # required_power_w = 1.12 * 10^11 * (distance_ly)^2
    # This folds receiver sensitivity into one visualization coefficient; it is
    # not a full radiometer-equation model for a specific FAST observing setup.
    df['required_power_w'] = 1.12e11 * (df['distance_ly'] ** 2)
    
    return df

if __name__ == "__main__":
    try:
        df = fetch_exoplanet_data()
        print("\n撈取到的前 2000 筆最近系外行星資料：")
        
        # 設定 pandas 顯示選項以漂亮地印出 DataFrame
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        
        print(df)
        
        # 輸出成 JavaScript 變數，方便前端 HTML 載入 (避免 CORS 問題)
        js_content = f"window.EXOPLANETS_DATA = {df.to_json(orient='records', force_ascii=False)};"
        with open("data.js", "w", encoding="utf-8") as f:
            f.write(js_content)
        print("已匯出資料至 data.js")
        
    except requests.exceptions.RequestException as e:
        print(f"API 請求失敗: {e}")
    except Exception as e:
        print(f"發生錯誤: {e}")
