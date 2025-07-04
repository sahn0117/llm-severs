# C:\llm_service\rag_system\scripts\vector_store.py

import os
import logging
from typing import List, Dict, Any
from pathlib import Path
import shutil
import time

# LangChain imports
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

class VectorStoreManager:
    def __init__(self, persist_directory: str, collection_name: str = "default_collection", embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        [修正] persist_directory 和 collection_name 變為必要/可選參數
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"載入嵌入模型: {embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.logger.info(f"初始化 ChromaDB: 目錄='{self.persist_directory}', 集合='{self.collection_name}'")
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )

    def add_documents(self, documents: List[Document], batch_size: int = 4000) -> List[str]:
        if not documents: return []
        total_docs = len(documents); all_ids = []
        self.logger.info(f"準備將 {total_docs} 個文檔分批加入集合 '{self.collection_name}'，每批大小: {batch_size}")
        for i in range(0, total_docs, batch_size):
            batch_documents = documents[i:i + batch_size]
            try:
                self.logger.info(f"正在處理批次 {i // batch_size + 1}...")
                ids = [f"doc_{i+j}_{hash(doc.page_content)}" for j, doc in enumerate(batch_documents)]
                self.vector_store.add_documents(documents=batch_documents, ids=ids)
                all_ids.extend(ids)
            except Exception as e:
                self.logger.error(f"處理批次時發生錯誤: {e}", exc_info=True); continue
        self.logger.info(f"所有批次處理完成，共成功添加 {len(all_ids)} / {total_docs} 個文檔。")
        return all_ids
    
    def get_relevant_context(self, query: str, k: int = 3, max_length: int = 2000) -> str:
        try:
            results_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
            context_parts = []
            current_length = 0
            for doc, score in results_with_scores:
                content = doc.page_content.strip()
                if current_length + len(content) <= max_length:
                    context_parts.append(content)
                    current_length += len(content)
                else: break
            return "\n\n---\n\n".join(context_parts)
        except Exception as e:
            self.logger.error(f"搜索失敗: {e}"); return ""

    def get_stats(self) -> Dict[str, Any]:
        try:
            count = self.vector_store._collection.count()
            return { "total_documents": count, "embedding_model": self.embedding_model_name, "persist_directory": self.persist_directory, "collection_name": self.collection_name }
        except Exception as e:
            self.logger.error(f"獲取統計信息失敗: {e}"); return {}