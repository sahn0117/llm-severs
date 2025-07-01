import os
import logging
from pathlib import Path
from typing import List, Dict, Any
import jieba
import re

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import (
    TextLoader, 
    PyPDFLoader, 
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader
)

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 設定中文文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        
        # 設定日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_single_document(self, file_path: str) -> List[Document]:
        """載入單個文檔"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"檔案不存在: {file_path}")
            return []
        
        try:
            # 根據檔案類型選擇載入器
            if file_path.suffix.lower() == '.txt':
                loader = TextLoader(str(file_path), encoding='utf-8')
            elif file_path.suffix.lower() == '.pdf':
                loader = PyPDFLoader(str(file_path))
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                loader = Docx2txtLoader(str(file_path))
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                loader = UnstructuredExcelLoader(str(file_path))
            elif file_path.suffix.lower() in ['.pptx', '.ppt']:
                loader = UnstructuredPowerPointLoader(str(file_path))
            else:
                self.logger.warning(f"不支援的檔案格式: {file_path.suffix}")
                return []
            
            # 載入文檔
            documents = loader.load()
            
            # 添加元數據
            for doc in documents:
                doc.metadata.update({
                    'source': str(file_path),
                    'filename': file_path.name,
                    'file_type': file_path.suffix.lower()
                })
            
            self.logger.info(f"成功載入文檔: {file_path.name}")
            return documents
            
        except Exception as e:
            self.logger.error(f"載入文檔失敗 {file_path}: {str(e)}")
            return []
    
    def load_directory(self, directory_path: str) -> List[Document]:
        """載入目錄中的所有文檔"""
        directory = Path(directory_path)
        
        if not directory.exists():
            self.logger.error(f"目錄不存在: {directory}")
            return []
        
        all_documents = []
        supported_extensions = {'.txt', '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt'}
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                documents = self.load_single_document(str(file_path))
                all_documents.extend(documents)
        
        self.logger.info(f"從目錄 {directory} 載入了 {len(all_documents)} 個文檔片段")
        return all_documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """分割文檔為小塊"""
        if not documents:
            return []
        
        # 預處理中文文本
        processed_docs = []
        for doc in documents:
            # 清理文本
            cleaned_content = self.clean_text(doc.page_content)
            
            if cleaned_content.strip():
                doc.page_content = cleaned_content
                processed_docs.append(doc)
        
        # 分割文檔
        split_docs = self.text_splitter.split_documents(processed_docs)
        
        self.logger.info(f"文檔分割完成，共 {len(split_docs)} 個片段")
        return split_docs
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多餘的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留中文、英文、數字、基本標點）
        text = re.sub(r'[^\u4e00-\u9fff\w\s.,!?;:()（）「」『』""''。，！？；：]', '', text)
        
        return text.strip()
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取關鍵詞"""
        # 使用 jieba 進行中文分詞
        words = jieba.cut(text)
        
        # 過濾停用詞和短詞
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', '自己', '這'}
        
        filtered_words = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # 統計詞頻
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 返回前 k 個高頻詞
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [word for word, freq in keywords]

# 測試用的主程式
if __name__ == "__main__":
    processor = DocumentProcessor()
    
    # 測試載入目錄
    docs_dir = r"C:\llm_service\rag_system\documents"
    documents = processor.load_directory(docs_dir)
    
    if documents:
        # 分割文檔
        split_docs = processor.split_documents(documents)
        print(f"載入了 {len(documents)} 個文檔，分割為 {len(split_docs)} 個片段")
        
        # 顯示第一個片段的內容
        if split_docs:
            print(f"\n第一個片段內容：\n{split_docs[0].page_content[:200]}...")
            print(f"元數據：{split_docs[0].metadata}")
    else:
        print("沒有找到任何文檔")
