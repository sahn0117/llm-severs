# C:\llm_service\rag_system\scripts\rag_service.py
# 版本: v5.0 - 純服務版 (無管理功能)

import os
import logging
from typing import List, Dict, Any
from pathlib import Path
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vector_store import VectorStoreManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        project_root = Path(__file__).parent.parent.parent
        
        static_db_path = str(project_root / "rag_system" / "embeddings" / "static_db")
        dynamic_db_path = str(project_root / "rag_system" / "embeddings" / "dynamic_db")
        
        logger.info("正在初始化 RAGService，準備載入知識庫...")
        
        try:
            self.static_vsm = VectorStoreManager(
                persist_directory=static_db_path, 
                collection_name="static_docs"
            )
        except Exception as e:
            logger.error(f"載入靜態知識庫失敗: {e}", exc_info=True)
            self.static_vsm = None
            
        try:
            self.dynamic_vsm = VectorStoreManager(
                persist_directory=dynamic_db_path,
                collection_name="dynamic_data"
            )
        except Exception as e:
            logger.error(f"載入動態知識庫失敗: {e}", exc_info=True)
            self.dynamic_vsm = None
            
        logger.info("RAG 服務初始化完成。")

    def query(self, query_text: str, k: int = 3, use_static: bool = True, use_dynamic: bool = True) -> Dict[str, Any]:
        all_context_parts = []
        
        if use_static and self.static_vsm:
            logger.info("正在查詢靜態知識庫...")
            static_context = self.static_vsm.get_relevant_context(query_text, k=k)
            if static_context:
                all_context_parts.append("--- 相關專業知識 ---\n" + static_context)
        
        if use_dynamic and self.dynamic_vsm:
            logger.info("正在查詢動態知識庫...")
            dynamic_context = self.dynamic_vsm.get_relevant_context(query_text, k=k)
            if dynamic_context:
                all_context_parts.append("--- 相關即時資訊 ---\n" + dynamic_context)
        
        if not all_context_parts:
            return {"has_context": False, "context": ""}
        
        return {
            "has_context": True,
            "context": "\n\n".join(all_context_parts)
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        return {
            "static_db": self.static_vsm.get_stats() if self.static_vsm else "Not loaded",
            "dynamic_db": self.dynamic_vsm.get_stats() if self.dynamic_vsm else "Not loaded"
        }