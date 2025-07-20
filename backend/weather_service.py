# C:\llm_service\backend\weather_service.py
# 版本: v24.2 - 修正循環匯入問題

import os
import sys
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- 路徑和日誌設定 ---
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "backend"))

# 這裡不應該有 "from weather_service import ..."
# 這是造成錯誤的那一行，現在已經被刪除

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaiwanWeatherService:
    def __init__(self):
        """初始化服務，包含 CWA 鄉鎮天氣預報 (F-C0032-001) 與即時天氣觀測 (O-A0003-001)"""
        # 從環境變數讀取 API Key
        # 注意：這個動作改到 __init__ 內部，確保 .env 在物件實例化時才被讀取
        from dotenv import load_dotenv
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            logger.info(f"成功從 {env_path} 載入環境變數。")
        else:
            logger.warning(f"[警告] 找不到 .env 檔案於 {env_path}，將嘗試從系統環境變數讀取。")
        
        self.api_key = os.getenv("CWA_API_KEY")
        if not self.api_key:
            logger.error("CWA_API_KEY 環境變數未設定！程式可能無法正常運作。")
            
        self.base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
        self.api_endpoint_forecast = "F-C0032-001" 
        self.api_endpoint_current = "O-A0003-001"
        
        self.LOCATIONS_TO_QUERY = [
            '臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市', '基隆市', '屏東縣'
        ]

    def _make_request(self, api_endpoint: str, extra_params: Optional[Dict[str, str]] = None) -> Optional[dict]:
        """通用型的 API 請求函式"""
        if not self.api_key: 
            logger.error("API Key 未設定，無法發送請求。")
            return None
        
        url = f"{self.base_url}/{api_endpoint}"
        
        params = {"Authorization": self.api_key}
        if extra_params:
            params.update(extra_params)
        
        try:
            response = requests.get(url, params=params, timeout=30)
            logger.info(f"正在請求 API URL: {response.url}")
            response.raise_for_status()
            data = response.json()
            if data.get("success") == "true":
                logger.info(f"成功從 API ({api_endpoint}) 獲取資料。")
                return data
            logger.warning(f"API ({api_endpoint}) 回應 success=false。")
            return None
        except requests.RequestException as e:
            logger.error(f"API ({api_endpoint}) 請求失敗: {e}")
            return None

    def get_weather_summary(self) -> Dict[str, Any]:
        """生成所有指定地區的天氣預報摘要"""
        forecast_params = {"locationName": ",".join(self.LOCATIONS_TO_QUERY)}
        all_data = self._make_request(self.api_endpoint_forecast, forecast_params)
        
        if not all_data:
            return {"success": False, "error": "無法從預報 API 獲取有效資料"}

        locations = all_data.get("records", {}).get("location", [])
        
        if not locations:
            logger.error("預報 API 回應成功，但未包含任何地區資料 (location 陣列為空)。")
            return {"success": False, "error": "預報 API 回應中缺少地區資料"}

        summary_data = []
        for loc in locations:
            location_name = loc.get("locationName")
            report = {"location_name": location_name}
            
            weather_elements = {el['elementName']: el['time'][0] for el in loc.get('weatherElement', [])}
            
            wx_param = weather_elements.get('Wx', {}).get('parameter', {})
            pop_param = weather_elements.get('PoP', {}).get('parameter', {})
            min_t_param = weather_elements.get('MinT', {}).get('parameter', {})
            max_t_param = weather_elements.get('MaxT', {}).get('parameter', {})
            ci_param = weather_elements.get('CI', {}).get('parameter', {})

            report.update({
                "weather_condition": wx_param.get('parameterName', 'N/A'),
                "rain_probability": int(pop_param.get('parameterName', -1)),
                "min_temperature": int(min_t_param.get('parameterName', -99)),
                "max_temperature": int(max_t_param.get('parameterName', -99)),
                "comfort_index": ci_param.get('parameterName', 'N/A'),
            })
            
            if location_name == "屏東縣":
                report["note"] = "这是整个屏东县的预报，适用于内埔乡"

            summary_data.append(report)
            
        return {"success": True, "data": summary_data}

    def get_current_weather(self, station_name: str) -> Dict[str, Any]:
        """獲取指定觀測站的即時天氣資料 (O-A0003-001)"""
        all_station_data = self._make_request(self.api_endpoint_current)

        if not all_station_data:
            return {"success": False, "error": "無法從即時觀測 API 獲取有效資料"}
        
        stations = all_station_data.get("records", {}).get("Station", [])
        if not stations:
            logger.error("即時觀測 API 回應成功，但未包含任何測站資料 (Station 陣列為空)。")
            return {"success": False, "error": "即時觀測 API 回應中缺少測站資料"}

        target_station = next((s for s in stations if s.get("StationName") == station_name), None)
        
        if not target_station:
            return {"success": False, "error": f"找不到名為 '{station_name}' 的觀測站"}

        weather_elements = target_station.get("WeatherElement", {})
        
        def clean_value(value, is_precipitation=False):
            """處理無效值"""
            try:
                val = float(value)
                if is_precipitation and val < 0: return 0.0
                if not is_precipitation and val < -90: return None
                return val
            except (ValueError, TypeError):
                return value if value else None

        now_precipitation = weather_elements.get("Now", {}).get("Precipitation", -99)

        result = {
            "station_name": target_station.get("StationName"),
            "station_id": target_station.get("StationId"),
            "observation_time": target_station.get("ObsTime", {}).get("DateTime"),
            "county": target_station.get("GeoInfo", {}).get("CountyName"),
            "town": target_station.get("GeoInfo", {}).get("TownName"),
            "weather": weather_elements.get("Weather"),
            "temperature_c": clean_value(weather_elements.get("AirTemperature")),
            "relative_humidity_percent": clean_value(weather_elements.get("RelativeHumidity")),
            "wind_speed_ms": clean_value(weather_elements.get("WindSpeed")),
            "wind_direction_deg": clean_value(weather_elements.get("WindDirection")),
            "precipitation_mm": clean_value(now_precipitation, is_precipitation=True),
        }

        return {"success": True, "data": result}

# --- 程式碼測試區 ---
if __name__ == "__main__":
    import json
    
    print("\n--- 初始化 TaiwanWeatherService ---")
    service = TaiwanWeatherService()

    if not service.api_key:
        print("\n[錯誤] 未能讀取到 CWA_API_KEY，請檢查 .env 檔案或系統環境變數。測試中止。")
        sys.exit(1)

    print("\n--- 測試【新功能】獲取'臺北'站的即時天氣 ---")
    current_weather_taipei = service.get_current_weather("臺北")
    if current_weather_taipei.get("success"):
        print(json.dumps(current_weather_taipei['data'], ensure_ascii=False, indent=2))
    else:
        print(f"查詢失敗: {current_weather_taipei.get('error')}")