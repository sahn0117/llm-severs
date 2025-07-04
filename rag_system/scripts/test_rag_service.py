# C:\llm_service\rag_system\scripts\test_rag_service.py

import sys
import os
import logging
from pathlib import Path
import json

# --- 設置路徑和日誌 ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 導入我們要測試的服務 ---
from rag_service import RAGService

def run_tests():
    """執行 RAGService 的完整測試流程"""
    logger.info("="*60)
    logger.info("啟動 RAGService 雙知識庫測試腳本")
    logger.info("="*60)

    # 1. 初始化 RAGService
    # ----------------------------------------------------
    try:
        logger.info("[步驟 1/5] 正在初始化 RAGService...")
        rag_service = RAGService()
        logger.info("[✓] RAGService 初始化成功。")
    except Exception as e:
        logger.error(f"[✗] RAGService 初始化失敗: {e}", exc_info=True)
        return

    # 2. 重建靜態知識庫
    # ----------------------------------------------------
    logger.info("\n[步驟 2/5] 正在重建靜態知識庫 (static_db)...")
    try:
        # 確保 documents 目錄下有檔案
        docs_dir = Path(__file__).parent.parent.parent / "rag_system" / "documents"
        if not any(docs_dir.iterdir()):
             logger.warning(f"'{docs_dir}' 目錄是空的，將建立一個空的靜態知識庫。")
        
        result_static = rag_service.rebuild_static_db()
        if result_static.get("success"):
            logger.info(f"[✓] 靜態知識庫重建成功: {result_static.get('message')}")
        else:
            logger.error(f"[✗] 靜態知識庫重建失敗: {result_static.get('error')}")
    except Exception as e:
        logger.error(f"[✗] 重建靜態知識庫時發生未預期錯誤: {e}", exc_info=True)

    # 3. 重建動態知識庫 (天氣)
    # ----------------------------------------------------
    logger.info("\n[步驟 3/5] 正在重建動態知識庫 (dynamic_db)...")
    try:
        # 確保 data 目錄下有檔案
        data_dir = Path(__file__).parent.parent.parent / "data"
        if not data_dir.exists() or not any(data_dir.iterdir()):
             logger.warning(f"'{data_dir}' 目錄不存在或為空，將建立一個空的天氣知識庫。")
             data_dir.mkdir(exist_ok=True) # 確保目錄存在

        result_dynamic = rag_service.rebuild_dynamic_db()
        if result_dynamic.get("success"):
            logger.info(f"[✓] 動態知識庫重建成功: {result_dynamic.get('message')}")
        else:
            logger.error(f"[✗] 動態知識庫重建失敗: {result_dynamic.get('error')}")
    except Exception as e:
        logger.error(f"[✗] 重建動態知識庫時發生未預期錯誤: {e}", exc_info=True)

    # 4. 驗證查詢
    # ----------------------------------------------------
    logger.info("\n[步驟 4/5] 正在驗證查詢功能...")
    
    # 測試只查詢靜態庫
    logger.info("\n--- 測試 4.1: 只查詢靜態庫 (關於 '專案管理') ---")
    static_query_result = rag_service.query("專案管理是什麼？", use_static=True, use_dynamic=False)
    if static_query_result.get("has_context"):
        logger.info("[✓] 成功從靜態庫中檢索到內容。")
        logger.info(f"內容預覽: {static_query_result['context'][:100]}...")
    else:
        logger.warning("[!] 未從靜態庫中找到相關內容。")

    # 測試只查詢動態庫
    logger.info("\n--- 測試 4.2: 只查詢動態庫 (關於 '高雄天氣') ---")
    dynamic_query_result = rag_service.query("高雄天氣", use_static=False, use_dynamic=True)
    if dynamic_query_result.get("has_context"):
        logger.info("[✓] 成功從動態庫中檢索到內容。")
        logger.info(f"內容預覽: {dynamic_query_result['context'][:100]}...")
    else:
        logger.warning("[!] 未從動態庫中找到相關內容。")

    # 測試聯合查詢
    logger.info("\n--- 測試 4.3: 聯合查詢 (關於 '天氣') ---")
    combined_query_result = rag_service.query("天氣", use_static=True, use_dynamic=True)
    if combined_query_result.get("has_context"):
        logger.info("[✓] 成功執行聯合查詢。")
        logger.info(f"內容預覽: {combined_query_result['context'][:200]}...")
        if "專業知識" in combined_query_result['context'] and "即時資訊" in combined_query_result['context']:
             logger.info("[✓] 驗證成功: 聯合查詢結果包含了兩個知識庫的內容。")
    else:
        logger.warning("[!] 聯合查詢未找到任何內容。")

    # 5. 顯示最終狀態
    # ----------------------------------------------------
    logger.info("\n[步驟 5/5] 顯示最終系統狀態...")
    final_status = rag_service.get_system_status()
    logger.info("\n--- RAG 系統最終狀態 ---")
    print(json.dumps(final_status, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run_tests()