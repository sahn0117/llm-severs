import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# LangChain imports
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

class VectorStoreManager:
    def __init__(self, persist_directory: str = None, embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        初始化向量資料庫管理器
        
        Args:
            persist_directory: 向量資料庫持久化目錄
            embedding_model: 嵌入模型名稱
        """
        self.persist_directory = persist_directory or r"C:\llm_service\rag_system\embeddings"
        self.embedding_model_name = embedding_model
        
        # 確保目錄存在
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # 設定日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 初始化嵌入模型
        self.logger.info(f"載入嵌入模型: {embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},  # 使用 CPU，如果有 GPU 可改為 'cuda'
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 初始化向量資料庫
        self.vector_store = None
        self.load_or_create_vector_store()
    
    def load_or_create_vector_store(self):
        """載入或建立向量資料庫"""
        try:
            # 檢查是否已存在向量資料庫
            if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
                self.logger.info("載入現有的向量資料庫...")
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                self.logger.info(f"成功載入向量資料庫，包含 {self.vector_store._collection.count()} 個文檔")
            else:
                self.logger.info("建立新的向量資料庫...")
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                self.logger.info("成功建立新的向量資料庫")
                
        except Exception as e:
            self.logger.error(f"載入/建立向量資料庫失敗: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文檔到向量資料庫"""
        if not documents:
            self.logger.warning("沒有文檔需要添加")
            return []
        
        try:
            self.logger.info(f"開始添加 {len(documents)} 個文檔到向量資料庫...")
            
            # 為每個文檔生成唯一 ID
            ids = [f"doc_{i}_{hash(doc.page_content)}" for i, doc in enumerate(documents)]
            
            # 添加文檔
            self.vector_store.add_documents(documents=documents, ids=ids)
            
            # 持久化
            self.vector_store.persist()
            
            self.logger.info(f"成功添加 {len(documents)} 個文檔")
            return ids
            
        except Exception as e:
            self.logger.error(f"添加文檔失敗: {str(e)}")
            raise
    
    def similarity_search(self, query: str, k: int = 5, score_threshold: float = 0.0) -> List[Document]:
        """相似度搜索"""
        if not self.vector_store:
            self.logger.error("向量資料庫未初始化")
            return []
        
        try:
            self.logger.info(f"搜索查詢: '{query}', 返回前 {k} 個結果")
            
            # 執行相似度搜索
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # 過濾低分結果
            filtered_results = [doc for doc, score in results if score >= score_threshold]
            
            self.logger.info(f"找到 {len(filtered_results)} 個相關文檔")
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"搜索失敗: {str(e)}")
            return []
    
    def get_relevant_context(self, query: str, k: int = 3, max_length: int = 2000) -> str:
        """獲取相關上下文"""
        relevant_docs = self.similarity_search(query, k=k)
        
        if not relevant_docs:
            return ""
        
        # 組合相關文檔內容
        context_parts = []
        current_length = 0
        
        for doc in relevant_docs:
            content = doc.page_content.strip()
            if current_length + len(content) <= max_length:
                context_parts.append(content)
                current_length += len(content)
            else:
                # 添加部分內容
                remaining_length = max_length - current_length
                if remaining_length > 100:  # 至少保留 100 字符
                    context_parts.append(content[:remaining_length] + "...")
                break
        
        context = "\n\n".join(context_parts)
        self.logger.info(f"組合上下文長度: {len(context)} 字符")
        
        return context
    
    def delete_documents(self, ids: List[str]) -> bool:
        """刪除文檔"""
        try:
            self.vector_store.delete(ids=ids)
            self.vector_store.persist()
            self.logger.info(f"成功刪除 {len(ids)} 個文檔")
            return True
        except Exception as e:
            self.logger.error(f"刪除文檔失敗: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取資料庫統計信息"""
        try:
            count = self.vector_store._collection.count()
            return {
                "total_documents": count,
                "embedding_model": self.embedding_model_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            self.logger.error(f"獲取統計信息失敗: {str(e)}")
            return {}
    
    def rebuild_index(self, documents: List[Document]) -> bool:
        """重建索引"""
        try:
            self.logger.info("開始重建向量資料庫索引...")
            
            # 刪除現有資料庫
            if os.path.exists(self.persist_directory):
                import shutil
                shutil.rmtree(self.persist_directory)
            
            # 重新建立
            self.load_or_create_vector_store()
            
            # 添加文檔
            if documents:
                self.add_documents(documents)
            
            self.logger.info("向量資料庫索引重建完成")
            return True
            
        except Exception as e:
            self.logger.error(f"重建索引失敗: {str(e)}")
            return False

# 測試用的主程式
if __name__ == "__main__":
    # 建立向量資料庫管理器
    vector_manager = VectorStoreManager()
    
    # 測試文檔
    test_docs = [
        Document(
            page_content="這是一個關於人工智能的文檔。人工智能是計算機科學的一個分支。",
            metadata={"source": "test1.txt", "type": "test"}
        ),
        Document(
            page_content="機器學習是人工智能的一個重要組成部分，它讓計算機能夠從數據中學習。",
            metadata={"source": "test2.txt", "type": "test"}
        )
    ]
    
    # 添加測試文檔
    ids = vector_manager.add_documents(test_docs)
    print(f"添加了 {len(ids)} 個文檔")
    
    # 測試搜索
    query = "什麼是人工智能？"
    context = vector_manager.get_relevant_context(query)
    print(f"\n查詢: {query}")
    print(f"相關上下文:\n{context}")
    
    # 顯示統計信息
    stats = vector_manager.get_stats()
    print(f"\n資料庫統計: {stats}")
