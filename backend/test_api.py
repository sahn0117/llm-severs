# C:\llm_service\backend\test_api.py
# 版本: vFinal.2 - 強化雙知識庫查詢驗證

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_static_rag_chat():
    """測試靜態 RAG 知識庫 (關於人工智能)"""
    print("\n=== [TEST] 1. 靜態 RAG 知識庫查詢 ===")
    
    # [修改] 將問題明確為「人工智能」，以配合後面的聯合測試
    query = "什麼是人工智能？"
    print(f"發送查詢: \"{query}\"")

    response = requests.post(f"{BASE_URL}/chat", json={"message": query})
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 靜態 RAG 查詢成功。")
        print(f"LLM 回應: {data.get('response', 'N/A')}")
        if "人工智能" in data.get('response', ''):
            print("[PASS] 驗證通過: 回應內容與靜態文件(人工智能)相關。")
        else:
            print("[FAIL] 驗證失敗: 回應內容似乎與人工智能無關。")
    else:
        print(f"[FAIL] 靜態 RAG 查詢失敗: {response.status_code} - {response.text}")


def test_dynamic_weather_chat():
    """測試動態天氣知識庫"""
    print("\n=== [TEST] 2. 動態天氣知識庫查詢 ===")
    
    weather_query = "我想知道今天屏東的天氣如何？"
    print(f"發送天氣查詢: \"{weather_query}\"")

    response = requests.post(f"{BASE_URL}/chat", json={"message": weather_query})
    
    if response.status_code == 200:
        data = response.json()
        llm_response = data.get('response', '')
        
        print(f"[OK] 天氣問答成功。")
        print(f"LLM 回應: {llm_response}")
        
        # [修改] 驗證回應是否同時包含「即時天氣」和「預報」的關鍵字
        if "即時天氣" in llm_response and "預報" in llm_response and "屏東" in llm_response:
            print("[PASS] 驗證通過: 回應中包含了屏東的即時天氣與預報資訊！")
        else:
            print("[FAIL] 驗證失敗: 回應中未能完整呈現即時天氣與預報資訊。")
    else:
        print(f"[FAIL] 天氣問答失敗: {response.status_code} - {response.text}")

def test_combined_rag_chat():
    """
    [核心修改]
    測試聯合查詢，同時提問靜態知識(AI)與動態知識(天氣)
    """
    print("\n=== [TEST] 3. 雙知識庫聯合查詢 (AI + 天氣) ===")
    
    # [核心修改] 改成您指定的多意圖問題
    query = "請簡單介紹一下什麼是人工智能，然後告訴我現在屏東的天氣怎麼樣，以及未來的預報？"
    print(f"發送聯合查詢: \"{query}\"")

    response = requests.post(f"{BASE_URL}/chat", json={"message": query})

    if response.status_code == 200:
        data = response.json()
        llm_response = data.get('response', '')
        print(f"[OK] 聯合查詢成功。")
        print(f"LLM 回應: {llm_response}")
        
        # [核心修改] 驗證回應是否同時包含兩邊的知識
        if "人工智能" in llm_response and "屏東" in llm_response and "即時天氣" in llm_response and "預報" in llm_response:
            print("[PASS] 驗證通過: 回應成功結合了靜態(AI)與動態(天氣)知識庫的資訊！")
        else:
            print("[FAIL] 驗證失敗: 回應未能體現雙知識庫的完整結合。")
    else:
        print(f"[FAIL] 聯合查詢失敗: {response.status_code} - {response.text}")


if __name__ == "__main__":
    print("="*60)
    print("  啟動 LLM 服務最終整合測試 (vFinal.2)")
    print("  請確保後端服務已啟動 (在另一個終端機執行: python backend/app.py)")
    print("="*60)
    
    try:
        # 依序執行三個核心測試
        test_static_rag_chat()
        test_dynamic_weather_chat()
        test_combined_rag_chat()
        
        print("\n🎉 恭喜！所有核心功能測試完成！您的雙知識庫 RAG 系統已可正常運作！")
        
    except requests.exceptions.ConnectionError:
        print("\n[FATAL] 無法連接到後端服務 (http://localhost:5000)，請確保服務已啟動。")
    except Exception as e:
        print(f"\n[FATAL] 測試過程中發生錯誤: {str(e)}")