# C:\llm_service\rag_system\scripts\document_loader.py
# 版本: v2.4 - 修正了 text_splitter 參數

import os
import logging
import json
from typing import List
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentLoader:
    def __init__(self, documents_dir: str):
        self.documents_dir = Path(documents_dir)
        self.supported_extensions = {'.pdf': self._load_pdf, '.txt': self._load_text, '.docx': self._load_docx, '.json': self._load_json}
        
        # [核心修正] 使用正確的參數名稱 chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200 # <-- 正確的參數名
        )

    def _load_pdf(self, file_path: str) -> List[Document]:
        try: loader = PyPDFLoader(file_path); return loader.load_and_split(self.text_splitter)
        except Exception as e: logger.error(f"載入 PDF 失敗: {file_path}, {e}"); return []

    def _load_text(self, file_path: str) -> List[Document]:
        try: loader = TextLoader(file_path, encoding='utf-8'); return loader.load_and_split(self.text_splitter)
        except Exception as e: logger.error(f"載入 TXT 失敗: {file_path}, {e}"); return []

    def _load_docx(self, file_path: str) -> List[Document]:
        try: loader = UnstructuredWordDocumentLoader(file_path); return loader.load_and_split(self.text_splitter)
        except Exception as e: logger.error(f"載入 DOCX 失敗: {file_path}, {e}"); return []
        
    def _load_json(self, file_path: str) -> List[Document]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f: data = json.load(f)
            text_content = self._json_to_text(data)
            if not text_content: return []
            docs = self.text_splitter.create_documents([text_content], metadatas=[{"source": str(file_path)}])
            return docs
        except Exception as e: logger.error(f"載入 JSON 失敗: {file_path}, {e}"); return []

    def _json_to_text(self, data: any, indent: int = 0) -> str:
        text_parts = []; prefix = "  " * indent
        if isinstance(data, dict):
            for key, value in data.items():
                if value is None or value == "" or key in ['success']: continue
                if isinstance(value, (dict, list)): text_parts.append(f"{prefix}{key}:"); text_parts.append(self._json_to_text(value, indent + 1))
                else: text_parts.append(f"{prefix}{key}: {str(value)}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)): text_parts.append(f"{prefix}- [{i+1}]:"); text_parts.append(self._json_to_text(item, indent + 1))
                else: text_parts.append(f"{prefix}- {str(item)}")
        else: return str(data)
        return "\n".join(text_parts)

    def load_document(self, file_path: str) -> List[Document]:
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()
        if extension not in self.supported_extensions:
            logger.debug(f"跳過不支援的格式: {file_path_obj.name}")
            return []
        logger.info(f"正在載入: {file_path_obj.name}")
        return self.supported_extensions[extension](str(file_path_obj))

    def load_all_documents(self, file_pattern: str = "*") -> List[Document]:
        all_documents = []
        logger.info(f"開始掃描目錄: {self.documents_dir}，模式: '{file_pattern}'")
        
        for file_path in self.documents_dir.rglob(file_pattern):
            if file_path.is_file():
                try:
                    documents = self.load_document(str(file_path))
                    all_documents.extend(documents)
                except Exception as e:
                    logger.error(f"處理檔案 {file_path.name} 時發生嚴重錯誤: {e}")
                    continue
        
        logger.info(f"目錄掃描完成，共載入 {len(all_documents)} 個文檔片段。")
        return all_documents