import requests
import json
import logging
from typing import Dict, Any, Optional
import sys
import os

# 添加 RAG 系統路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rag_system', 'scripts'))

from rag_service import RAGService

class LLMService:
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434",
                 model_name: str = "llama3.1:8b",
                 rag_enabled: bool = True):
        """
        初始化 LLM 服務
        
        Args:
            ollama_url: Ollama 服務地址
            model_name: 使用的模型名稱
            rag_enabled: 是否啟用 RAG
        """
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.rag_enabled = rag_enabled
        
        # 設定日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化 RAG 服務
        if self.rag_enabled:
            try:
                self.rag_service = RAGService()
                self.logger.info("RAG 服務初始化成功")
            except Exception as e:
                self.logger.error(f"RAG 服務初始化失敗: {str(e)}")
                self.rag_enabled = False
                self.rag_service = None
        else:
            self.rag_service = None
        
        self.logger.info(f"LLM 服務初始化完成 (RAG: {'啟用' if self.rag_enabled else '停用'})")
    
    def check_ollama_status(self) -> bool:
        """檢查 Ollama 服務狀態"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def call_ollama(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """呼叫 Ollama API"""
        try:
            # 構建請求數據
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            # 添加系統提示（如果有）
            if system_prompt:
                data["system"] = system_prompt
            
            self.logger.info(f"呼叫 Ollama API，模型: {self.model_name}")
            
            # 發送請求
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                self.logger.error(f"Ollama API 錯誤: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"呼叫 Ollama API 失敗: {str(e)}")
            return None
    
    def generate_response(self, user_query: str, conversation_history: list = None) -> Dict[str, Any]:
        """
        生成回應（整合 RAG）
        
        Args:
            user_query: 用戶查詢
            conversation_history: 對話歷史
            
        Returns:
            包含回應和元數據的字典
        """
        try:
            self.logger.info(f"處理用戶查詢: {user_query}")
            
            # 初始化結果
            result = {
                "response": "",
                "user_query": user_query,
                "rag_used": False,
                "rag_context": "",
                "sources": [],
                "processing_steps": []
            }
            
            # 步驟 1: RAG 檢索（如果啟用）
            rag_context = ""
            if self.rag_enabled and self.rag_service:
                result["processing_steps"].append("正在檢索相關知識...")
                
                rag_result = self.rag_service.query(user_query, k=3, max_context_length=1500)
                
                if rag_result["has_context"]:
                    rag_context = rag_result["context"]
                    result["rag_used"] = True
                    result["rag_context"] = rag_context
                    result["sources"] = rag_result["sources"]
                    result["processing_steps"].append(f"找到 {rag_result['num_relevant_docs']} 個相關文檔")
                else:
                    result["processing_steps"].append("未找到相關知識，使用模型原生知識回答")
            
            # 步驟 2: 構建 LLM 提示
            result["processing_steps"].append("正在生成回應...")
            
            if rag_context:
                # 有 RAG 上下文的提示
                prompt = self._build_rag_prompt(user_query, rag_context, conversation_history)
                system_prompt = """你是一個有用的AI助手。請根據提供的上下文信息來回答用戶的問題。
如果上下文中包含相關信息，請優先使用這些信息來回答。
如果上下文中沒有足夠的信息，請結合你的知識來提供有用的回答。
請用繁體中文回答，語氣要友善和專業。"""
            else:
                # 沒有 RAG 上下文的提示
                prompt = self._build_simple_prompt(user_query, conversation_history)
                system_prompt = """你是一個有用的AI助手。請用繁體中文回答用戶的問題，語氣要友善和專業。"""
            
            # 步驟 3: 呼叫 LLM
            llm_response = self.call_ollama(prompt, system_prompt)
            
            if llm_response:
                result["response"] = llm_response.strip()
                result["processing_steps"].append("回應生成完成")
                self.logger.info("LLM 回應生成成功")
            else:
                result["response"] = "抱歉，我現在無法處理您的請求。請稍後再試。"
                result["processing_steps"].append("LLM 服務暫時不可用")
                self.logger.error("LLM 回應生成失敗")
            
            return result
            
        except Exception as e:
            self.logger.error(f"生成回應失敗: {str(e)}")
            return {
                "response": "抱歉，處理您的請求時發生錯誤。",
                "user_query": user_query,
                "rag_used": False,
                "rag_context": "",
                "sources": [],
                "processing_steps": [f"錯誤: {str(e)}"],
                "error": str(e)
            }
    
    def _build_rag_prompt(self, user_query: str, context: str, conversation_history: list = None) -> str:
        """構建包含 RAG 上下文的提示"""
        prompt_parts = []
        
        # 添加上下文
        prompt_parts.append("以下是相關的背景資料：")
        prompt_parts.append("=" * 50)
        prompt_parts.append(context)
        prompt_parts.append("=" * 50)
        prompt_parts.append("")
        
        # 添加對話歷史（如果有）
        if conversation_history:
            prompt_parts.append("對話歷史：")
            for msg in conversation_history[-3:]:  # 只保留最近 3 輪對話
                role = "用戶" if msg.get("role") == "user" else "助手"
                prompt_parts.append(f"{role}: {msg.get('content', '')}")
            prompt_parts.append("")
        
        # 添加當前問題
        prompt_parts.append(f"用戶問題: {user_query}")
        prompt_parts.append("")
        prompt_parts.append("請根據上述背景資料回答用戶的問題。如果背景資料中沒有相關信息，請結合你的知識來回答：")
        
        return "\n".join(prompt_parts)
    
    def _build_simple_prompt(self, user_query: str, conversation_history: list = None) -> str:
        """構建簡單提示"""
        prompt_parts = []
        
        # 添加對話歷史（如果有）
        if conversation_history:
            prompt_parts.append("對話歷史：")
            for msg in conversation_history[-3:]:  # 只保留最近 3 輪對話
                role = "用戶" if msg.get("role") == "user" else "助手"
                prompt_parts.append(f"{role}: {msg.get('content', '')}")
            prompt_parts.append("")
        
        # 添加當前問題
        prompt_parts.append(f"用戶問題: {user_query}")
        
        return "\n".join(prompt_parts)
    
    def get_available_models(self) -> list:
        """獲取可用的模型列表"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            else:
                return []
        except Exception as e:
            self.logger.error(f"獲取模型列表失敗: {str(e)}")
            return []
    
    def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "ollama_status": self.check_ollama_status(),
            "current_model": self.model_name,
            "rag_enabled": self.rag_enabled,
            "rag_status": self.rag_service is not None,
            "available_models": self.get_available_models()
        }

# 測試用的主程式
if __name__ == "__main__":
    # 建立 LLM 服務
    llm_service = LLMService()
    
    # 檢查服務狀態
    status = llm_service.get_service_status()
    print("LLM 服務狀態:")
    print(f"  Ollama 狀態: {'正常' if status['ollama_status'] else '異常'}")
    print(f"  當前模型: {status['current_model']}")
    print(f"  RAG 啟用: {'是' if status['rag_enabled'] else '否'}")
    print(f"  可用模型: {status['available_models']}")
    
    # 測試查詢
    if status['ollama_status']:
        test_query = "什麼是機器學習？"
        print(f"\n測試查詢: {test_query}")
        
        result = llm_service.generate_response(test_query)
        
        print(f"RAG 使用: {'是' if result['rag_used'] else '否'}")
        if result['rag_used']:
            print(f"知識來源: {result['sources']}")
        print(f"回應: {result['response']}")
    else:
        print("\nOllama 服務未啟動，請先啟動 Ollama")
