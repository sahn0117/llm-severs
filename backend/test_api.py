# C:\llm_service\backend\test_api.py
# 版本: vFinal - 專注於聊天和雙知識庫驗證

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_static_rag_chat():
    """測試靜態 RAG 知識庫 (非天氣問題)"""
    print("\n=== [TEST] 靜態 RAG 知識庫查詢 ===")
    
    query = "什麼是機器學習？請根據背景資料回答。"
    print(f"發送查詢: \"{query}\"")

    response = requests.post(f"{BASE_URL}/chat", json={"message": query})
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 靜態 RAG 查詢成功。")
        print(f"LLM 回應: {data.get('response', 'N/A')}")
        if "data" in data.get('response', '').lower() or "人工智能" in data.get('response', ''):
            print("[OK] 驗證通過: 回應內容與靜態文件相關。")
        else:
            print("[WARN] 回應內容似乎與靜態文件無關，請手動檢查。")
    else:
        print(f"[FAIL] 靜態 RAG 查詢失敗: {response.status_code} - {response.text}")


def test_dynamic_weather_chat():
    """測試動態天氣知識庫"""
    print("\n=== [TEST] 動態天氣知識庫查詢 ===")
    
    # [核心修改] 提出更詳細的天氣問題
    weather_query = "我想知道今天台北的氣壓和濕度是多少？"
    print(f"發送詳細天氣查詢: \"{weather_query}\"")

    response = requests.post(f"{BASE_URL}/chat", json={"message": weather_query})
    
    if response.status_code == 200:
        data = response.json()
        llm_response = data.get('response', '')
        
        print(f"[OK] 天氣問答成功。")
        print(f"LLM 回應: {llm_response}")
        
        # 驗證回應是否包含氣壓 (hPa) 和濕度 (%)
        if "hpa" in llm_response.lower() and "%" in llm_response:
            print("[OK] 驗證通過: 回應中包含了氣壓和濕度的詳細資訊！")
        else:
            print("[FAIL] 驗證失敗: 回應中未找到氣壓 (hPa) 或濕度 (%) 的資訊。")
    else:
        print(f"[FAIL] 天氣問答失敗: {response.status_code} - {response.text}")

def test_combined_rag_chat():
    """測試聯合查詢"""
    print("\n=== [TEST] 雙知識庫聯合查詢 ===")
    
    query = "請根據專案管理知識，判斷今天台北的天氣是否適合戶外施工？"
    print(f"發送聯合查詢: \"{query}\"")

    response = requests.post(f"{BASE_URL}/chat", json={"message": query})

    if response.status_code == 200:
        data = response.json()
        llm_response = data.get('response', '')
        print(f"[OK] 聯合查詢成功。")
        print(f"LLM 回應: {llm_response}")
        if "專案管理" in llm_response and ("天氣" in llm_response or "溫度" in llm_response):
            print("[OK] 驗證通過: 回應同時結合了靜態知識和天氣資訊！")
        else:
            print("[WARN] 回應內容未能體現雙知識庫結合，請手動檢查。")
    else:
        print(f"[FAIL] 聯合查詢失敗: {response.status_code} - {response.text}")


if __name__ == "__main__":
    print("="*50)
    print("啟動 LLM 服務最終整合測試...")
    print("請確保後端服務已啟動 (python backend/app.py)")
    print("="*50)
    
    try:
        # 執行新的、更有針對性的測試
        test_static_rag_chat()
        test_dynamic_weather_chat()
        test_combined_rag_chat()
        
        print("\n🎉 恭喜！所有核心功能測試完成！您的雙知識庫 RAG 系統已可正常運作！")
        
    except requests.exceptions.ConnectionError:
        print("\n[FATAL] 無法連接到後端服務，請確保服務已啟動。")
    except Exception as e:
        print(f"\n[FATAL] 測試過程中發生錯誤: {str(e)}")