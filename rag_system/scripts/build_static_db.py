# C:\llm_service\rag_system\scripts\build_static_db.py
"""
只做靜態資料庫更新(rag)
"""

import sys
import os
import logging
import shutil
from pathlib import Path
import json
import time

# --- 設置路徑和日誌 ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from document_loader import DocumentLoader
from vector_store import VectorStoreManager

# --- 配置 ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATIC_DOCS_DIR = str(PROJECT_ROOT / "rag_system" / "documents")
STATIC_DB_DIR = str(PROJECT_ROOT / "rag_system" / "embeddings" / "static_db")

def main():
    logger.info("==================================================")
    logger.info("RAG 靜態知識庫重建腳本啟動")
    logger.info("==================================================")

    try:
        # 1. 刪除舊的靜態資料庫目錄
        if os.path.exists(STATIC_DB_DIR):
            logger.warning(f"正在刪除舊的靜態資料庫目錄: {STATIC_DB_DIR}")
            shutil.rmtree(STATIC_DB_DIR)
            time.sleep(0.5) # 給系統一點時間
            logger.info("舊靜態資料庫目錄已成功刪除。")
        else:
            logger.info("靜態資料庫目錄不存在，無需刪除。")

        # 2. 初始化靜態 VectorStoreManager
        logger.info("正在初始化靜態向量資料庫管理器...")
        static_vsm = VectorStoreManager(
            persist_directory=STATIC_DB_DIR,
            collection_name="static_docs"
        )
        logger.info("靜態 VectorStoreManager 初始化完成。")

        # 3. 處理靜態文件目錄
        logger.info(f"--- 正在處理靜態文檔目錄: {STATIC_DOCS_DIR} ---")
        static_loader = DocumentLoader(STATIC_DOCS_DIR)
        static_documents = static_loader.load_all_documents(file_pattern="*") # 索引所有文件
        
        if static_documents:
            logger.info(f"偵測到 {len(static_documents)} 個靜態文檔片段，準備加入知識庫...")
            static_vsm.add_documents(static_documents)
            logger.info(f"成功添加 {len(static_documents)} 個靜態文檔片段。")
        else:
            logger.warning(f"在 '{STATIC_DOCS_DIR}' 中未找到可處理的靜態檔案。")

        # 4. 顯示最終統計
        final_stats = static_vsm.get_stats()
        logger.info(f"靜態知識庫重建完成！最終統計: {json.dumps(final_stats, indent=2, ensure_ascii=False)}")

    except Exception as e:
        logger.error(f"靜態知識庫重建腳本執行失敗: {e}", exc_info=True)

if __name__ == "__main__":
    main()