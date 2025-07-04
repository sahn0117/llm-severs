import os
import logging
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
import io

import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechToTextService:
    """語音轉文字服務"""
    
    def __init__(self):
        """初始化語音轉文字服務"""
        self.recognizer = sr.Recognizer()
        
        # 檢查 ffmpeg 是否可用 (用於音頻格式轉換)
        if not which("ffmpeg"):
            logger.warning("ffmpeg 未找到，某些音頻格式可能無法處理")
        
        # 支援的音頻格式
        self.supported_formats = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm'}
        
        logger.info("語音轉文字服務初始化完成")
    
    def transcribe_audio_file(self, 
                             file_path: str, 
                             language: str = "zh-TW") -> Dict[str, Any]:
        """
        轉錄音頻文件
        
        Args:
            file_path: 音頻文件路徑
            language: 語言代碼 (zh-TW, zh-CN, en-US 等)
            
        Returns:
            轉錄結果
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "音頻文件不存在",
                    "text": ""
                }
            
            if file_path.suffix.lower() not in self.supported_formats:
                return {
                    "success": False,
                    "error": f"不支援的音頻格式: {file_path.suffix}",
                    "text": ""
                }
            
            # 轉換音頻格式為 WAV (如果需要)
            wav_file_path = self._convert_to_wav(str(file_path))
            
            # 使用 speech_recognition 進行轉錄
            with sr.AudioFile(wav_file_path) as source:
                # 調整環境噪音
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # 錄製音頻
                audio = self.recognizer.record(source)
            
            # 進行語音識別
            try:
                # 使用 Google 語音識別 (需要網路連接)
                text = self.recognizer.recognize_google(audio, language=language)
                
                # 清理臨時文件
                if wav_file_path != str(file_path):
                    Path(wav_file_path).unlink(missing_ok=True)
                
                return {
                    "success": True,
                    "text": text,
                    "language": language,
                    "confidence": "high"  # Google API 不提供置信度分數
                }
                
            except sr.UnknownValueError:
                return {
                    "success": False,
                    "error": "無法識別音頻內容",
                    "text": ""
                }
            except sr.RequestError as e:
                return {
                    "success": False,
                    "error": f"語音識別服務錯誤: {str(e)}",
                    "text": ""
                }
                
        except Exception as e:
            logger.error(f"轉錄音頻文件失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    def transcribe_audio_data(self, 
                             audio_data: bytes, 
                             format: str = "wav",
                             language: str = "zh-TW") -> Dict[str, Any]:
        """
        轉錄音頻數據
        
        Args:
            audio_data: 音頻數據 (bytes)
            format: 音頻格式
            language: 語言代碼
            
        Returns:
            轉錄結果
        """
        try:
            # 將音頻數據保存為臨時文件
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # 轉錄音頻文件
            result = self.transcribe_audio_file(temp_file_path, language)
            
            # 清理臨時文件
            Path(temp_file_path).unlink(missing_ok=True)
            
            return result
            
        except Exception as e:
            logger.error(f"轉錄音頻數據失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    def _convert_to_wav(self, file_path: str) -> str:
        """
        將音頻文件轉換為 WAV 格式
        
        Args:
            file_path: 原始音頻文件路徑
            
        Returns:
            WAV 文件路徑
        """
        file_path = Path(file_path)
        
        # 如果已經是 WAV 格式，直接返回
        if file_path.suffix.lower() == '.wav':
            return str(file_path)
        
        try:
            # 使用 pydub 轉換音頻格式
            audio = AudioSegment.from_file(str(file_path))
            
            # 轉換為 WAV 格式
            wav_file_path = file_path.with_suffix('.wav')
            audio.export(str(wav_file_path), format="wav")
            
            logger.info(f"音頻格式轉換完成: {file_path} -> {wav_file_path}")
            return str(wav_file_path)
            
        except Exception as e:
            logger.error(f"音頻格式轉換失敗: {str(e)}")
            # 如果轉換失敗，返回原始文件路徑
            return str(file_path)
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        獲取支援的語言列表
        
        Returns:
            語言代碼和名稱的字典
        """
        return {
            "zh-TW": "繁體中文 (台灣)",
            "zh-CN": "簡體中文 (中國)",
            "en-US": "英語 (美國)",
            "en-GB": "英語 (英國)",
            "ja-JP": "日語 (日本)",
            "ko-KR": "韓語 (韓國)",
            "fr-FR": "法語 (法國)",
            "de-DE": "德語 (德國)",
            "es-ES": "西班牙語 (西班牙)",
            "it-IT": "義大利語 (義大利)"
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        獲取服務資訊
        
        Returns:
            服務資訊
        """
        return {
            "service_name": "Speech-to-Text Service",
            "supported_formats": list(self.supported_formats),
            "supported_languages": self.get_supported_languages(),
            "engine": "Google Speech Recognition",
            "requires_internet": True
        }

# 測試函數
def test_speech_to_text():
    """測試語音轉文字服務"""
    service = SpeechToTextService()
    
    # 獲取服務資訊
    info = service.get_service_info()
    print("語音轉文字服務資訊:")
    print(f"服務名稱: {info['service_name']}")
    print(f"支援格式: {info['supported_formats']}")
    print(f"支援語言數量: {len(info['supported_languages'])}")
    print(f"識別引擎: {info['engine']}")
    print(f"需要網路: {info['requires_internet']}")
    
    return service

# ======================================================
# 以下是修改好的、用於獨立測試這個檔案的主程式
# ======================================================
if __name__ == "__main__":
    # 1. 初始化服務並打印基本資訊
    stt_service = SpeechToTextService()
    
    print("\n" + "="*50)
    info = stt_service.get_service_info()
    print("服務資訊:")
    for key, value in info.items():
        if isinstance(value, list):
            print(f"  - {key}: {', '.join(value)}")
        elif isinstance(value, dict):
            print(f"  - {key}: {len(value)} 種語言")
        else:
            print(f"  - {key}: {value}")
    print("="*50 + "\n")

    # 2. 定義測試檔案的路徑
    #    請確保這個路徑是您電腦上的實際路徑
    test_file_path = r"C:\Users\AIOTL-M08\Desktop\llm_service\data\test_audio.wav"
    
    print(f"--- 開始測試從文件轉錄 ---")
    print(f"測試檔案路徑: {test_file_path}")

    # 3. 檢查測試檔案是否存在
    if os.path.exists(test_file_path):
        # 4. 如果檔案存在，就呼叫轉錄函式
        #    注意：我們呼叫的是您程式中定義的 transcribe_audio_file 函式
        result = stt_service.transcribe_audio_file(test_file_path, language="zh-TW")
        
        # 5. 根據轉錄結果打印不同訊息
        if result.get("success"):
            print("\n[✓] 轉錄成功！")
            print(f"    - 語言: {result.get('language')}")
            print(f"    - 結果: {result.get('text')}")
        else:
            print("\n[✗] 轉錄失敗！")
            print(f"    - 原因: {result.get('error')}")
    else:
        # 如果檔案不存在，打印提示
        print(f"\n[!] 測試文件不存在: {test_file_path}")
        print("    請將一個名為 'test_audio.wav' 的音訊檔放置在 data 目錄中才能進行測試。")

    print("\n--- 測試結束 ---")