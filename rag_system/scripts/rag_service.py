# C:\Users\AIOTL-M08\Desktop\llm_service\rag_system\scripts\rag_service.py (已修改版本)

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# --- [修改] 動態計算專案根目錄 ---
# __file__ 是當前檔案的路徑 (rag_service.py)
# .parent 是上一層目錄 (scripts)
# .parent.parent 是上上層目錄 (rag_system)
# .parent.parent.parent 是專案根目錄 (llm_service)
PROJECT_ROOT = Path(__file__).parent.parent.parent

from document_loader import DocumentProcessor
from vector_store import VectorStoreManager

class RAGService:
    def __init__(self, 
                 documents_dir: str = None,
                 embeddings_dir: str = None,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        初始化 RAG 服務
        """
        # --- [修改] 使用動態路徑 ---
        # 如果外部沒有傳入路徑，就使用計算出來的專案預設路徑
        self.documents_dir = documents_dir or str(PROJECT_ROOT / "rag_system" / "documents")
        self.embeddings_dir = embeddings_dir or str(PROJECT_ROOT / "rag_system" / "embeddings")
        
        # 確保目錄存在
        Path(self.documents_dir).mkdir(parents=True, exist_ok=True)
        Path(self.embeddings_dir).mkdir(parents=True, exist_ok=True)
        
        # 設定日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化組件
        self.document_processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        # --- [修改] 將正確的 embeddings_dir 傳遞給 VectorStoreManager ---
        self.vector_manager = VectorStoreManager(persist_directory=self.embeddings_dir)
        
        self.logger.info("RAG 服務初始化完成")
    
    def load_documents_from_directory(self) -> bool:
        """從目錄載入所有文檔到向量資料庫"""
        try:
            self.logger.info(f"開始從目錄載入文檔: {self.documents_dir}")
            
            # 載入文檔
            documents = self.document_processor.load_directory(self.documents_dir)
            
            if not documents:
                self.logger.warning("沒有找到任何文檔")
                return False
            
            # 分割文檔
            split_documents = self.document_processor.split_documents(documents)
            
            if not split_documents:
                self.logger.warning("文檔分割後沒有有效內容")
                return False
            
            # 添加到向量資料庫
            ids = self.vector_manager.add_documents(split_documents)
            
            self.logger.info(f"成功載入 {len(documents)} 個文檔，分割為 {len(split_documents)} 個片段")
            return True
            
        except Exception as e:
            self.logger.error(f"載入文檔失敗: {str(e)}", exc_info=True) # exc_info=True 可以打印更詳細的錯誤
            return False
    
    def add_single_document(self, file_path: str) -> bool:
        """添加單個文檔"""
        try:
            self.logger.info(f"添加單個文檔: {file_path}")
            
            documents = self.document_processor.load_single_document(file_path)
            
            if not documents:
                self.logger.warning(f"無法載入文檔: {file_path}")
                return False
            
            split_documents = self.document_processor.split_documents(documents)
            
            if not split_documents:
                self.logger.warning("文檔分割後沒有有效內容")
                return False
            
            ids = self.vector_manager.add_documents(split_documents)
            
            self.logger.info(f"成功添加文檔，分割為 {len(split_documents)} 個片段")
            return True
            
        except Exception as e:
            self.logger.error(f"添加文檔失敗: {str(e)}", exc_info=True)
            return False
    
    def query(self, question: str, k: int = 3, max_context_length: int = 2000) -> Dict[str, Any]:
        """查詢 RAG 系統"""
        try:
            self.logger.info(f"RAG 查詢: {question}")
            
            context = self.vector_manager.get_relevant_context(
                query=question, 
                k=k, 
                max_length=max_context_length
            )
            
            relevant_docs = self.vector_manager.similarity_search(question, k=k)
            
            result = {
                "context": context,
                "has_context": bool(context.strip()),
                "num_relevant_docs": len(relevant_docs),
                "sources": [doc.metadata.get("source", "unknown") for doc in relevant_docs],
                "query": question
            }
            
            self.logger.info(f"RAG 查詢完成，找到 {len(relevant_docs)} 個相關文檔")
            return result
            
        except Exception as e:
            self.logger.error(f"RAG 查詢失敗: {str(e)}", exc_info=True)
            return {
                "context": "", "has_context": False, "num_relevant_docs": 0,
                "sources": [], "query": question, "error": str(e)
            }
    
    def rebuild_knowledge_base(self) -> bool:
        """重建知識庫"""
        try:
            self.logger.info("開始重建知識庫...")
            
            documents = self.document_processor.load_directory(self.documents_dir)
            
            if not documents:
                self.logger.warning("沒有找到任何文檔")
                return False

            split_documents = self.document_processor.split_documents(documents)
            
            success = self.vector_manager.rebuild_index(split_documents)
            
            if success:
                self.logger.info("知識庫重建完成")
            else:
                self.logger.error("知識庫重建失敗")
            
            return success
            
        except Exception as e:
            self.logger.error(f"重建知識庫失敗: {str(e)}", exc_info=True)
            return False
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """獲取知識庫統計信息"""
        try:
            vector_stats = self.vector_manager.get_stats()
            
            doc_files = []
            if os.path.exists(self.documents_dir):
                supported_extensions = {'.txt', '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt'}
                for file_path in Path(self.documents_dir).rglob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                        doc_files.append({
                            "name": file_path.name, "path": str(file_path),
                            "size": file_path.stat().st_size, "type": file_path.suffix.lower()
                        })
            
            return {
                "vector_database": vector_stats,
                "document_files": {"count": len(doc_files), "files": doc_files},
                "directories": {"documents": self.documents_dir, "embeddings": self.embeddings_dir}
            }
            
        except Exception as e:
            self.logger.error(f"獲取統計信息失敗: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索文檔"""
        try:
            relevant_docs = self.vector_manager.similarity_search(query, k=limit)
            
            results = []
            for doc in relevant_docs:
                results.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "unknown")
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"搜索文檔失敗: {str(e)}", exc_info=True)
            return []

# 測試用的主程式
if __name__ == "__main__":
    # 建立 RAG 服務 (現在會自動使用正確的路徑)
    rag_service = RAGService()
    
    # 檢查知識庫狀態
    stats = rag_service.get_knowledge_base_stats()
    print("知識庫統計:")
    print(f"  向量資料庫文檔數: {stats.get('vector_database', {}).get('total_documents', 0)}")
    print(f"  文檔檔案數: {stats.get('document_files', {}).get('count', 0)}")
    
    # 如果沒有文檔，嘗試載入
    if stats.get('vector_database', {}).get('total_documents', 0) == 0:
        print("\n嘗試載入文檔...")
        success = rag_service.load_documents_from_directory()
        if success:
            print("文檔載入成功")
            # 重新獲取統計數據以更新顯示
            stats = rag_service.get_knowledge_base_stats()
            print(f"  更新後向量資料庫文檔數: {stats.get('vector_database', {}).get('total_documents', 0)}")
        else:
            print("文檔載入失敗或沒有找到文檔")
            print(f"請將文檔放入目錄: {rag_service.documents_dir}")
    
    # 測試查詢
    test_query = "什麼是人工智能？"
    result = rag_service.query(test_query)
    
    print(f"\n測試查詢: {test_query}")
    print(f"找到相關內容: {result['has_context']}")
    if result['has_context']:
        print(f"上下文: {result['context'][:200]}...")
        # 打印來源，確保它來自正確的文件
        print(f"來源: {result['sources']}")