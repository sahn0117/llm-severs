# C:\llm_service\backend\weather_scheduler.py
# 版本: Final - 純粹的天氣數據生成排程器 (不觸發 RAG 重建)

import os
import sys
import json
import logging
import schedule
from datetime import datetime
from pathlib import Path
# subprocess 不需要了，因為不再由它觸發 build_dbs.py

# --- 路徑和導入設置 ---
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "backend"))
from dotenv import load_dotenv
load_dotenv(project_root / ".env")
from weather_service import TaiwanWeatherService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeatherScheduler:
    def __init__(self):
        self.weather_service = TaiwanWeatherService()
        self.data_dir = project_root / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
    def run_update_task(self):
        """執行更新，只生成一份乾淨的全台摘要檔"""
        logger.info("=== 開始生成最新的天氣摘要 ===")
        try:
            summary = self.weather_service.get_weather_summary()
            
            if summary.get("success"):
                # 1. 儲存完整的 JSON 摘要，方便偵錯
                summary_file = self.data_dir / 'weather_summary_latest.json'
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2)
                
                # 2. 生成 LLM 專用的文字檔
                text_parts = ["=== 台灣主要城市天氣摘要 ==="]
                for city_data in summary['data']:
                    station_name = city_data.get('station_name_queried') # 確保這裡取對了鍵
                    
                    text_parts.append(f"\n【{station_name}】")
                    if "error" in city_data:
                        text_parts.append(f"  - 狀態: {city_data['error']}")
                    else:
                        city_from_api = city_data.get('city_from_api', station_name)
                        temp = city_data.get('temperature', -99)
                        humidity = city_data.get('humidity', -99)
                        pressure = city_data.get('pressure', -99)
                        wind = city_data.get('wind_speed', -99)
                        desc = city_data.get('description', 'N/A')
                        
                        text_parts.append(f"  - 地區: {city_from_api}")
                        if temp > -99: text_parts.append(f"  - 溫度: {temp}°C")
                        if humidity > -99: text_parts.append(f"  - 濕度: {humidity}%")
                        if pressure > -99: text_parts.append(f"  - 氣壓: {pressure} hPa")
                        if wind > -99: text_parts.append(f"  - 風速: {wind} m/s")
                        text_parts.append(f"  - 天氣狀況: {desc}")

                text_parts.append(f"\n\n資料來源：中央氣象署\n更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                final_text = "\n".join(text_parts)
                
                llm_file = self.data_dir / 'weather_for_llm.txt'
                with open(llm_file, 'w', encoding='utf-8') as f:
                    f.write(final_text)
                logger.info(f"成功生成摘要檔案: {llm_file}")
            else:
                logger.error(f"獲取天氣摘要失敗: {summary.get('error')}")

        except Exception as e:
            logger.error(f"執行更新任務時發生錯誤: {e}", exc_info=True)
            
        logger.info("=== 天氣摘要更新完成 ===")

    def start(self):
        """啟動排程器"""
        schedule.every().hour.do(self.run_update_task)
        logger.info("設定排程任務: 每小時執行一次更新。")
        logger.info("排程器啟動，首次更新將在 5 秒後執行...")
        time.sleep(5)
        self.run_update_task()

        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    scheduler = WeatherScheduler()
    scheduler.start()