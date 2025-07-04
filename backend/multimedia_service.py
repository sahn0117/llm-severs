import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from speech_to_text import SpeechToTextService
from ocr_service import OCRService

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultimediaService:
    """多媒體處理整合服務"""
    
    def __init__(self):
        """初始化多媒體服務"""
        try:
            # 初始化語音轉文字服務
            self.speech_service = SpeechToTextService()
            logger.info("語音轉文字服務初始化成功")
        except Exception as e:
            logger.error(f"語音轉文字服務初始化失敗: {str(e)}")
            self.speech_service = None
        
        try:
            # 初始化 OCR 服務
            self.ocr_service = OCRService()
            logger.info("OCR 服務初始化成功")
        except Exception as e:
            logger.error(f"OCR 服務初始化失敗: {str(e)}")
            self.ocr_service = None
        
        logger.info("多媒體處理整合服務初始化完成")
    
    def process_audio(self, 
                     file_path: str = None,
                     audio_data: bytes = None,
                     format: str = "wav",
                     language: str = "zh-TW") -> Dict[str, Any]:
        """
        處理音頻文件或數據
        
        Args:
            file_path: 音頻文件路徑
            audio_data: 音頻數據 (bytes)
            format: 音頻格式
            language: 語言代碼
            
        Returns:
            處理結果
        """
        if not self.speech_service:
            return {
                "success": False,
                "error": "語音轉文字服務不可用",
                "text": "",
                "service": "speech_to_text"
            }
        
        try:
            if file_path:
                result = self.speech_service.transcribe_audio_file(file_path, language)
            elif audio_data:
                result = self.speech_service.transcribe_audio_data(audio_data, format, language)
            else:
                return {
                    "success": False,
                    "error": "必須提供 file_path 或 audio_data",
                    "text": "",
                    "service": "speech_to_text"
                }
            
            result["service"] = "speech_to_text"
            return result
            
        except Exception as e:
            logger.error(f"音頻處理失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "service": "speech_to_text"
            }
    
    def process_image(self, 
                     file_path: str = None,
                     image_data: bytes = None,
                     language: str = "chi_tra+eng",
                     preprocess: bool = True) -> Dict[str, Any]:
        """
        處理圖片文件或數據
        
        Args:
            file_path: 圖片文件路徑
            image_data: 圖片數據 (bytes)
            language: OCR 語言
            preprocess: 是否進行圖片預處理
            
        Returns:
            處理結果
        """
        if not self.ocr_service:
            return {
                "success": False,
                "error": "OCR 服務不可用",
                "text": "",
                "service": "ocr"
            }
        
        try:
            if file_path:
                result = self.ocr_service.extract_text_from_image(file_path, language, preprocess)
            elif image_data:
                result = self.ocr_service.extract_text_from_image_data(image_data, language, preprocess)
            else:
                return {
                    "success": False,
                    "error": "必須提供 file_path 或 image_data",
                    "text": "",
                    "service": "ocr"
                }
            
            result["service"] = "ocr"
            return result
            
        except Exception as e:
            logger.error(f"圖片處理失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "service": "ocr"
            }
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """
        獲取支援的格式
        
        Returns:
            支援的格式資訊
        """
        formats = {
            "audio": [],
            "image": []
        }
        
        if self.speech_service:
            formats["audio"] = list(self.speech_service.supported_formats)
        
        if self.ocr_service:
            formats["image"] = list(self.ocr_service.supported_formats)
        
        return formats
    
    def get_supported_languages(self) -> Dict[str, Any]:
        """
        獲取支援的語言
        
        Returns:
            支援的語言資訊
        """
        languages = {
            "speech_to_text": {},
            "ocr": {}
        }
        
        if self.speech_service:
            languages["speech_to_text"] = self.speech_service.get_supported_languages()
        
        if self.ocr_service:
            languages["ocr"] = self.ocr_service.get_language_info()
        
        return languages
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        獲取服務狀態
        
        Returns:
            服務狀態資訊
        """
        status = {
            "speech_to_text": {
                "available": self.speech_service is not None,
                "info": None
            },
            "ocr": {
                "available": self.ocr_service is not None,
                "info": None
            }
        }
        
        if self.speech_service:
            try:
                status["speech_to_text"]["info"] = self.speech_service.get_service_info()
            except Exception as e:
                status["speech_to_text"]["error"] = str(e)
        
        if self.ocr_service:
            try:
                status["ocr"]["info"] = self.ocr_service.get_service_info()
            except Exception as e:
                status["ocr"]["error"] = str(e)
        
        return status

# 測試函數
def test_multimedia_service():
    """測試多媒體處理服務"""
    service = MultimediaService()
    
    # 獲取服務狀態
    status = service.get_service_status()
    print("多媒體處理服務狀態:")
    print(f"語音轉文字可用: {status['speech_to_text']['available']}")
    print(f"OCR 可用: {status['ocr']['available']}")
    
    # 獲取支援的格式
    formats = service.get_supported_formats()
    print(f"支援的音頻格式: {formats['audio']}")
    print(f"支援的圖片格式: {formats['image']}")
    
    # 獲取支援的語言
    languages = service.get_supported_languages()
    print(f"語音轉文字支援語言數量: {len(languages['speech_to_text'])}")
    print(f"OCR 支援語言數量: {len(languages['ocr'])}")
    
    return service

if __name__ == "__main__":
    test_multimedia_service()
