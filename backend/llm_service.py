# C:\llm_service\backend\llm_service.py
# 版本: vFinal 3.6 - 加入回答後處理

import requests
import json
import logging
from typing import Dict, Any, Optional
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rag_system', 'scripts'))
from rag_service import RAGService

class LLMService:
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434",
                 model_name: str = "llama3.1:8b",
                 rag_enabled: bool = True):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.rag_enabled = rag_enabled
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        if self.rag_enabled:
            try:
                self.rag_service = RAGService()
                self.logger.info("RAG 服務初始化成功")
            except Exception as e:
                self.logger.error(f"RAG 服務初始化失敗: {str(e)}"); self.rag_enabled = False; self.rag_service = None
        else:
            self.rag_service = None
        self.logger.info(f"LLM 服務初始化完成 (RAG: {'啟用' if self.rag_enabled else '停用'})")
    
    def call_ollama(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        try:
            data = { "model": self.model_name, "prompt": prompt, "stream": False, "options": { "temperature": 0.7, "top_p": 0.9, "top_k": 40 } }
            if system_prompt: data["system"] = system_prompt
            response = requests.post(f"{self.ollama_url}/api/generate", json=data, timeout=60)
            if response.status_code == 200: return response.json().get("response", "")
            else: self.logger.error(f"Ollama API 錯誤: {response.status_code} - {response.text}"); return None
        except Exception as e: self.logger.error(f"呼叫 Ollama API 失敗: {str(e)}"); return None

    def generate_response(self, user_query: str, conversation_history: list = None, use_rag_static: bool = True, use_rag_dynamic: bool = False) -> Dict[str, Any]:
        try:
            self.logger.info(f"處理查詢: '{user_query}' (靜態RAG: {use_rag_static}, 動態RAG: {use_rag_dynamic})")
            
            result = { "response": "", "user_query": user_query, "rag_used": False, "rag_context": "", "sources": [] }
            
            rag_context = ""
            use_any_rag = use_rag_static or use_rag_dynamic
            
            if self.rag_enabled and self.rag_service and use_any_rag:
                rag_result = self.rag_service.query(
                    user_query, 
                    use_static=use_rag_static,
                    use_dynamic=use_rag_dynamic
                )
                if rag_result.get("has_context"):
                    rag_context = rag_result["context"]
                    result["rag_used"] = True
                    result["rag_context"] = rag_context
            
            if rag_context:
                prompt = self._build_rag_prompt(user_query, rag_context, conversation_history)
                system_prompt = "你是一個有用的AI助理。請根據以下提供的「背景資料」來回答用戶的問題。這些資料比你的內部知識更新，請優先使用。"
            else:
                prompt = self._build_simple_prompt(user_query, conversation_history)
                system_prompt = "你是一個有用的AI助理。請用繁體中文回答用戶的問題。"
            
            llm_response = self.call_ollama(prompt, system_prompt)
            
            if llm_response:
                # [核心修正] 對 LLM 的回答進行後處理，統一用字
                processed_response = llm_response.strip().replace("臺", "台")
                result["response"] = processed_response
            else:
                result["response"] = "抱歉，處理請求時發生錯誤。"
            
            return result
        except Exception as e:
            self.logger.error(f"生成回應失敗: {e}", exc_info=True)
            return { "response": "抱歉，發生內部錯誤。", "error": str(e) }

    def _build_rag_prompt(self, user_query: str, context: str, conversation_history: list = None) -> str:
        prompt_parts = ["=== 背景資料 ===", context, "=" * 18, ""]
        if conversation_history:
            prompt_parts.append("--- 對話歷史 ---")
            for msg in conversation_history[-3:]: prompt_parts.append(f"{'用戶' if msg.get('role') == 'user' else '助手'}: {msg.get('content', '')}")
            prompt_parts.append("")
        prompt_parts.append(f"用戶問題: {user_query}")
        prompt_parts.append("\n請根據上述背景資料和對話歷史，回答用戶的問題：")
        return "\n".join(prompt_parts)

    def _build_simple_prompt(self, user_query: str, conversation_history: list = None) -> str:
        prompt_parts = []
        if conversation_history:
            prompt_parts.append("--- 對話歷史 ---")
            for msg in conversation_history[-3:]: prompt_parts.append(f"{'用戶' if msg.get('role') == 'user' else '助手'}: {msg.get('content', '')}")
            prompt_parts.append("")
        prompt_parts.append(f"用戶問題: {user_query}")
        return "\n".join(prompt_parts)

    def get_service_status(self) -> Dict[str, Any]:
        return { "ollama_status": self.check_ollama_status(), "current_model": self.model_name, "rag_enabled": self.rag_enabled }