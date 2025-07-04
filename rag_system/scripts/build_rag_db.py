# C:\llm_service\rag_system\scripts\build_dbs.py
# 版本: Final - 純動態庫重建控制

"""
動態更新資料庫(rag)
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
STATIC_DOCS_DIR = str(PROJECT_ROOT / "rag_system" / "documents") # 靜態來源目錄
DYNAMIC_DATA_DIR = str(PROJECT_ROOT / "data") # 動態來源目錄

STATIC_DB_DIR = str(PROJECT_ROOT / "rag_system" / "embeddings" / "static_db") # 靜態庫路徑
DYNAMIC_DB_DIR = str(PROJECT_ROOT / "rag_system" / "embeddings" / "dynamic_db") # 動態庫路徑

def build_dynamic_database():
    """單獨處理動態知識庫的邏輯，用於自動更新"""
    logger.info("-" * 20)
    logger.info("開始處理動態知識庫: dynamic_data")
    logger.info(f"來源目錄: {DYNAMIC_DATA_DIR}")
    logger.info(f"檔案模式: 'weather_for_llm.txt'")
    logger.info(f"目標路徑: {DYNAMIC_DB_DIR}")

    if os.path.exists(DYNAMIC_DB_DIR):
        logger.warning(f"正在刪除舊的 'dynamic_data' 資料庫...")
        shutil.rmtree(DYNAMIC_DB_DIR)
        time.sleep(0.5)
    
    vsm = VectorStoreManager(
        persist_directory=DYNAMIC_DB_DIR,
        collection_name="dynamic_data"
    )
    
    loader = DocumentLoader(DYNAMIC_DATA_DIR)
    documents = loader.load_all_documents(file_pattern="weather_for_llm.txt") # 精準匹配
    
    if documents:
        vsm.add_documents(documents)
    else:
        logger.warning(f"在 '{DYNAMIC_DATA_DIR}' 中未找到 'weather_for_llm.txt' 檔案。")
        
    stats = vsm.get_stats()
    logger.info(f"動態知識庫 'dynamic_data' 處理完成。統計: {stats}")
    logger.info("-" * 20)


def main():
    logger.info("="*50)
    logger.info("RAG 知識庫重建腳本啟動")
    logger.info("==================================================")

    # [核心修改] 解析命令列參數
    # 如果運行 'python build_dbs.py dynamic' -> 只更新動態庫
    # 如果運行 'python build_dbs.py static' -> 需要手動執行 build_static_db.py
    # 如果不帶參數 -> 默認會運行 build_dynamic_database，但這個腳本主要是被 weather_scheduler 調用
    
    # 這裡的 main 函式將作為一個總的控制器，如果被直接調用，它會處理動態庫
    # 靜態庫的處理邏輯將完全由 build_static_db.py 負責
    
    build_type = "dynamic" # 預設只處理動態庫
    if len(sys.argv) > 1:
        if sys.argv[1] == "dynamic":
            build_type = "dynamic"
        elif sys.argv[1] == "static":
            logger.error("錯誤: 'static' 類型現在應使用獨立腳本 'build_static_db.py' 運行。")
            logger.error("請運行 'python build_static_db.py' 而不是 'python build_dbs.py static'。")
            sys.exit(1)
        else:
            logger.warning(f"未知的參數 '{sys.argv[1]}'，預設將重建動態知識庫。")

    if build_type == "dynamic":
        build_dynamic_database() # 執行動態知識庫的重建邏輯
    
    logger.info("="*50)
    logger.info("所有指定知識庫重建完成！")
    logger.info("==================================================")

if __name__ == "__main__":
    main()