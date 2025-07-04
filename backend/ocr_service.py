import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import io

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRService:
    """OCR (光學字元識別) 服務"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """初始化 OCR 服務"""
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif os.name == 'nt':
            default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if Path(default_path).exists():
                pytesseract.pytesseract.tesseract_cmd = default_path
        
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
        self.default_lang = 'chi_tra+eng'
        
        try:
            pytesseract.get_tesseract_version()
            logger.info("OCR 服務初始化完成")
        except Exception as e:
            logger.error(f"Tesseract 初始化失敗: {e}")
            raise

    def extract_text_from_image(self, image_path: str, lang: Optional[str] = None, preprocess: bool = False) -> Dict[str, Any]:
        """從圖片文件中提取文字"""
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                return {"success": False, "error": "圖片文件不存在"}
            
            if image_path.suffix.lower() not in self.supported_formats:
                return {"success": False, "error": f"不支援的圖片格式: {image_path.suffix}"}

            target_lang = lang if lang is not None else self.default_lang
            
            image = Image.open(image_path)

            if preprocess:
                image = self._preprocess_image(image)

            custom_config = r'--psm 11 --oem 1'
            
            text = pytesseract.image_to_string(image, lang=target_lang, config=custom_config)
            
            return {"success": True, "text": text.strip(), "language": target_lang}
        
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract 未安裝或未在系統 PATH 中。")
            return {"success": False, "error": "Tesseract is not installed or it's not in your PATH."}
        except Exception as e:
            logger.error(f"從圖片提取文字失敗: {str(e)}")
            return {"success": False, "error": str(e)}

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """圖片預處理以提高 OCR 準確度"""
        try:
            image = image.convert('L')
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2)
            return image
        except Exception as e:
            logger.warning(f"圖片預處理失敗，使用原始圖片: {str(e)}")
            return image

    # ======================================================
    # ↓↓↓ 以下是為您新增的函式 ↓↓↓
    # ======================================================
    def get_language_info(self) -> Dict[str, str]:
        """
        獲取常用語言代碼和名稱的對應
        
        Returns:
            語言資訊字典
        """
        return {
            "eng": "英文",
            "chi_tra": "繁體中文",
            "chi_sim": "簡體中文",
            "jpn": "日文",
            "kor": "韓文",
            "fra": "法文",
            "deu": "德文",
            "spa": "西班牙文",
            "ita": "義大利文",
            "rus": "俄文"
        }

    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        try:
            version = str(pytesseract.get_tesseract_version())
            available_languages = pytesseract.get_languages(config='')
        except Exception:
            version = "Unknown"
            available_languages = []
        
        return {
            "service_name": "OCR Service",
            "engine": "Tesseract",
            "version": version,
            "supported_formats": list(self.supported_formats),
            "available_languages": available_languages,
            "language_info": self.get_language_info() # 呼叫新增的函式
        }

# ======================================================
# 主測試區塊 (無需修改)
# ======================================================
if __name__ == "__main__":
    try:
        ocr_service = OCRService()
        print("\n[✓] OCR 服務初始化成功！")
    except Exception as e:
        print(f"[✗] OCR 服務初始化失敗: {e}")
        print("\n[!] 請檢查 Tesseract OCR 是否已正確安裝，並且其路徑是否在系統的 PATH 環境變數中。")
        exit()

    # 定義測試檔案的路徑 (請確保這是您那張海報圖片的路徑)
    test_file_path = r"C:\Users\AIOTL-M08\Desktop\llm_service\data\test_image.jpg"
    
    print(f"\n--- 開始測試從圖片文件識別 (使用 PSM 11, OEM 1) ---")
    print(f"測試圖片路徑: {test_file_path}")

    if os.path.exists(test_file_path):
        result = ocr_service.extract_text_from_image(test_file_path, lang='chi_sim+chi_tra', preprocess=False)
        
        if result.get("success"):
            print("\n[✓] 圖片識別成功！")
            print(f"    - 語言: {result.get('language')}")
            print(f"    - 原始結果:\n---\n{result.get('text')}\n---")
        else:
            print("\n[✗] 圖片識別失敗！")
            print(f"    - 原因: {result.get('error')}")
    else:
        print(f"\n[!] 測試文件不存在: {test_file_path}")

    print("\n--- 測試結束 ---")