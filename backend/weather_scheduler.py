# C:\llm_service\backend\weather_scheduler.py
# 版本: v24.5 - 修正觀測站對應名稱

import os
import sys
import json
import logging
import schedule
import time
from datetime import datetime
from pathlib import Path

# --- 路徑和導入設置 ---
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "backend"))
from weather_service import TaiwanWeatherService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeatherScheduler:
    def __init__(self):
        self.weather_service = TaiwanWeatherService()
        self.data_dir = project_root / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
        # 建立「預報地區」到「代表觀測站」的對應表
        self.location_to_station_map = {
            '臺北市': '臺北',
            '新北市': '新北',   # <--- 修正：將 '板橋' 改為 '新北'
            '桃園市': '新屋',   # <--- 修正：將 '桃園' 改為 '新屋'
            '臺中市': '臺中',
            '臺南市': '臺南',
            '高雄市': '高雄',
            '基隆市': '基隆',
            '屏東縣': '屏東'
        }
        
    def run_update_task(self):
        """執行更新，生成包含預報(含舒適度)和即時觀測的混合摘要"""
        logger.info("=== [排程器] 開始生成最新的混合天氣摘要 (預報+觀測) ===")
        try:
            forecast_summary = self.weather_service.get_weather_summary()
            
            if not forecast_summary.get("success"):
                logger.error(f"[排程器] 獲取天气預報摘要失敗: {forecast_summary.get('error')}")
                return

            text_parts = ["=== 台灣主要地区即時天氣與未來12小時預報摘要 ==="]
            
            for city_forecast in forecast_summary['data']:
                location_name = city_forecast.get('location_name')
                station_name = self.location_to_station_map.get(location_name)
                
                display_name = location_name
                if location_name == '屏東縣':
                    display_name = '屏東内埔 (參考屏東縣預報與屏東市觀測)'
                elif location_name == '新北市':
                    display_name = '新北市 (參考新北站觀測)'
                elif location_name == '桃園市':
                    display_name = '桃園市 (參考新屋站觀測)'
                
                text_parts.append(f"\n【{display_name}】")

                if station_name:
                    current_weather = self.weather_service.get_current_weather(station_name)
                    if current_weather.get("success"):
                        current_data = current_weather['data']
                        obs_time_str = current_data.get('observation_time', 'N/A').split('T')[1].split('+')[0]
                        temp = current_data.get('temperature_c', 'N/A')
                        rh = current_data.get('relative_humidity_percent', 'N/A')
                        precip = current_data.get('precipitation_mm', 'N/A')
                        
                        text_parts.append(f"  [即時天氣 @ {obs_time_str}]")
                        text_parts.append(f"    - 溫度: {temp}°C | 濕度: {rh}% | 降雨: {precip}mm")
                    else:
                        logger.warning(f"無法獲取 '{station_name}' 的即時天氣: {current_weather.get('error')}")
                        text_parts.append("  [即時天氣] (無法取得)")

                text_parts.append("  [未來12小時預報]")
                condition = city_forecast.get('weather_condition', '未知')
                rain_prob = city_forecast.get('rain_probability', -1)
                min_temp = city_forecast.get('min_temperature', -99)
                max_temp = city_forecast.get('max_temperature', -99)
                comfort = city_forecast.get('comfort_index', '未知')
                
                text_parts.append(f"    - 狀況: {condition} | 降雨機率: {rain_prob}%")
                if min_temp > -99 and max_temp > -99:
                    text_parts.append(f"    - 溫度範圍: {min_temp}°C 至 {max_temp}°C")
                text_parts.append(f"    - 舒適度: {comfort}")

            text_parts.append(f"\n\n資料來源：中央氣象署 (即時觀測 O-A0003-001 + 鄉鎮預報 F-C0032-001)\n報告生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            final_text = "\n".join(text_parts)
            
            llm_file = self.data_dir / 'weather_for_llm.txt'
            with open(llm_file, 'w', encoding='utf-8') as f:
                f.write(final_text)
            logger.info(f"成功生成 LLM 專用混合天氣摘要檔案: {llm_file}")

        except Exception as e:
            logger.error(f"[排程器] 執行更新任务时发生严重错误: {e}", exc_info=True)
            
        logger.info("=== [排程器] 混合天氣摘要更新完成 ===")

    def start_continuous_mode(self):
        """(舊功能) 啟動連續執行的排程器"""
        logger.info("排程器啟動 (連續模式)...")
        logger.info("設定排程任务: 每小時執行一次更新。")
        schedule.every().hour.do(self.run_update_task)
        
        logger.info("首次更新将在 5 秒後執行...")
        time.sleep(5)
        self.run_update_task()

        logger.info("進入主排程迴圈...")
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    scheduler = WeatherScheduler()

    if len(sys.argv) > 1 and sys.argv[1] == 'update':
        logger.info("偵測到 'update' 參數，執行單次更新任務...")
        scheduler.run_update_task()
        logger.info("單次任務執行完畢，程式結束。")
    else:
        logger.info("未偵測到 'update' 參數，啟動連續排程模式...")
        scheduler.start_continuous_mode()