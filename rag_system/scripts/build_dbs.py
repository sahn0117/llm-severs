# C:\llm_service\rag_system\scripts\build_dbs.py
# 版本: v3.3 - 精準索引版

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
DYNAMIC_DATA_DIR = str(PROJECT_ROOT / "data")
STATIC_DB_DIR = str(PROJECT_ROOT / "rag_system" / "embeddings" / "static_db")
DYNAMIC_DB_DIR = str(PROJECT_ROOT / "rag_system" / "embeddings" / "dynamic_db")

def build_database(db_path: str, collection_name: str, source_dir: str, file_pattern: str = "*"):
    """建立或重建單個知識庫的通用函數，增加 file_pattern 參數"""
    logger.info("-" * 20)
    logger.info(f"開始處理知識庫: {collection_name}")
    logger.info(f"來源目錄: {source_dir}")
    logger.info(f"檔案模式: '{file_pattern}'")
    logger.info(f"目標路徑: {db_path}")

    if os.path.exists(db_path):
        logger.warning(f"正在刪除舊的 '{collection_name}' 資料庫...")
        shutil.rmtree(db_path)
        time.sleep(0.5)
    
    vsm = VectorStoreManager(
        persist_directory=db_path,
        collection_name=collection_name
    )
    
    # 使用 DocumentLoader 的一個新方法來載入特定模式的檔案
    loader = DocumentLoader(source_dir)
    documents = loader.load_all_documents(file_pattern=file_pattern) # 傳入模式
    
    if documents:
        vsm.add_documents(documents)
    else:
        logger.warning(f"在 '{source_dir}' 中未找到符合 '{file_pattern}' 模式的檔案。")
        
    stats = vsm.get_stats()
    logger.info(f"知識庫 '{collection_name}' 處理完成。統計: {stats}")
    logger.info("-" * 20)

def main():
    logger.info("="*50); logger.info("啟動 RAG 雙知識庫重建腳本"); logger.info("="*50)
    
    # 1. 重建靜態知識庫 (處理所有支援檔案)
    build_database(STATIC_DB_DIR, "static_docs", STATIC_DOCS_DIR, "*")
    
    # 2. 重建動態知識庫 ([核心優化] 只處理所有以 _for_llm.txt 結尾的檔案)
    build_database(DYNAMIC_DB_DIR, "dynamic_data", DYNAMIC_DATA_DIR, "*_for_llm.txt")
    
    logger.info("="*50); logger.info("所有知識庫重建完成！"); logger.info("="*50)

if __name__ == "__main__":
    main()