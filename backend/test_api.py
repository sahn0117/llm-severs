import requests
import json

# API 基礎 URL
BASE_URL = "http://localhost:5000/api"

def test_chat_api():
    """測試聊天 API"""
    print("=== 測試聊天 API ===")
    
    # 第一次對話
    response1 = requests.post(f"{BASE_URL}/chat", json={
        "message": "你好，請介紹一下自己"
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"✅ 第一次對話成功")
        print(f"回應: {data1['response'][:100]}...")
        print(f"Session ID: {data1['session_id']}")
        
        session_id = data1['session_id']
        
        # 第二次對話（使用相同 session_id）
        response2 = requests.post(f"{BASE_URL}/chat", json={
            "message": "剛才我問了什麼問題？",
            "session_id": session_id
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"✅ 第二次對話成功")
            print(f"回應: {data2['response'][:100]}...")
        else:
            print(f"❌ 第二次對話失敗: {response2.text}")
    else:
        print(f"❌ 第一次對話失敗: {response1.text}")

def test_conversations_api():
    """測試對話列表 API"""
    print("\n=== 測試對話列表 API ===")
    
    response = requests.get(f"{BASE_URL}/conversations")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 獲取對話列表成功")
        print(f"總對話數: {data['total']}")
        
        if data['conversations']:
            conv = data['conversations'][0]
            print(f"第一個對話: {conv['title']}")
            print(f"訊息數量: {conv['message_count']}")
            
            # 測試獲取對話詳情
            session_id = conv['session_id']
            detail_response = requests.get(f"{BASE_URL}/conversations/{session_id}")
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                print(f"✅ 獲取對話詳情成功")
                print(f"訊息數量: {len(detail_data['messages'])}")
            else:
                print(f"❌ 獲取對話詳情失敗: {detail_response.text}")
    else:
        print(f"❌ 獲取對話列表失敗: {response.text}")

def test_search_api():
    """測試搜索 API"""
    print("\n=== 測試搜索 API ===")
    
    response = requests.get(f"{BASE_URL}/search", params={"q": "你好"})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 搜索成功")
        print(f"搜索結果數: {data['total']}")
    else:
        print(f"❌ 搜索失敗: {response.text}")

def test_status_api():
    """測試狀態 API"""
    print("\n=== 測試狀態 API ===")
    
    response = requests.get(f"{BASE_URL}/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 獲取狀態成功")
        print(f"Ollama 狀態: {'正常' if data['llm_service']['ollama_status'] else '異常'}")
        print(f"RAG 啟用: {'是' if data['llm_service']['rag_enabled'] else '否'}")
        print(f"總對話數: {data['database']['total_conversations']}")
        print(f"總訊息數: {data['database']['total_messages']}")
    else:
        print(f"❌ 獲取狀態失敗: {response.text}")

if __name__ == "__main__":
    print("開始測試 LLM 服務 API...")
    print("請確保後端服務已啟動 (python backend/app.py)")
    
    try:
        test_status_api()
        test_chat_api()
        test_conversations_api()
        test_search_api()
        
        print("\n🎉 所有測試完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到後端服務，請確保服務已啟動")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")
