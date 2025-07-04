# C:\llm_service\backend\weather_service.py
# 版本: v13.0 - 基於真實 API 結構的最終版

import os
import sys
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- 路徑和日誌設定 ---
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "backend"))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaiwanWeatherService:
    def __init__(self):
        """初始化服務，只使用最可靠的 API 和精確的站點名稱。"""
        self.api_key = os.getenv("CWA_API_KEY")
        if not self.api_key:
            logger.error("CWA_API_KEY 未設定！")
            
        self.base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
        self.api_endpoint = "O-A0001-001"
        
        # [核心] 請根據您 debug_stations.py 的輸出，確認這些站名是否都存在！
        # 這裡列出的是最常見的代表性站名。
        self.CITIES_MAPPING = {
            '台北': '臺北',
            '新北': '板橋',
            '桃園': '桃園',
            '台中': '臺中',
            '台南': '臺南',
            '高雄': '高雄',
            '基隆': '基隆'
        }

    def _make_request(self) -> Optional[dict]:
        if not self.api_key: return None
        url = f"{self.base_url}/{self.api_endpoint}"
        params = {"Authorization": self.api_key, "elementName": "TEMP,HUMD,PRES,WDIR,WDSD,Weather"}
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            logger.info(f"成功從 API ({self.api_endpoint}) 獲取資料。")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API 請求失敗: {e}")
            return None

    def get_weather_summary(self) -> Dict[str, Any]:
        """生成天氣摘要"""
        all_data = self._make_request()
        if not (all_data and all_data.get("success") == "true"):
            return {"success": False, "error": "無法從 API 獲取資料"}

        stations_data_pool = {
            loc.get("locationName"): loc for loc in all_data.get("records", {}).get("location", [])
        }
        
        summary_data = []
        for city_alias, station_name in self.CITIES_MAPPING.items():
            report = {"city_alias": city_alias, "station_name_queried": station_name}
            
            station_data = stations_data_pool.get(station_name)
            
            if station_data:
                weather_elements = {
                    el.get("elementName"): el.get("elementValue") 
                    for el in station_data.get("weatherElement", [])
                }
                
                # [核心修正] 從 station_data 的 parameter 欄位獲取縣市名
                city_name_from_api = "未知"
                for param in station_data.get("parameter", []):
                    if param.get("parameterName") == "CITY":
                        city_name_from_api = param.get("parameterValue")
                        break
                
                report["city_from_api"] = city_name_from_api
                report["temperature"] = float(weather_elements.get("TEMP", -99))
                report["humidity"] = int(float(weather_elements.get("HUMD", -99)) * 100) # 濕度是 0-1
                report["pressure"] = float(weather_elements.get("PRES", -99))
                report["wind_speed"] = float(weather_elements.get("WDSD", -99))
                report["description"] = weather_elements.get("Weather", "N/A")
            else:
                report["error"] = f"在 API 回應中找不到觀測站 '{station_name}'"
                
            summary_data.append(report)
            
        return {"success": True, "data": summary_data}