本地 LLM RAG 服務應用(本地版)
這是一個完整的、基於本地大型語言模型 (LLM) 的全端應用程式。它整合了檢索增強生成 (RAG) 技術，能夠結合靜態文件知識庫和動態即時資訊（如天氣），提供更精準、更有根據的對話體驗。

---

##  主要功能

*   **本地 LLM 支援**: 透過 [Ollama](https://ollama.com/) 支援本地運行各種開源大型語言模型（如 Llama 3.1）。
*   **雙知識庫 RAG 系統**:
    *   **靜態知識庫**: 可索引您提供的 PDF、Word、TXT 等文件，作為核心知識。
    *   **動態知識庫**: 可定期更新即時資訊（如天氣預報），供 LLM 查詢。
*   **智慧判斷**: 後端 API 可根據使用者問題，智慧決定是否啟用 RAG，以及使用哪個知識庫。
*   **天氣整合**: 內建天氣排程器，自動從台灣中央氣象署 (CWA) 獲取天氣資訊，並更新動態知識庫。
*   **多媒體處理 (可擴展)**: 已包含語音轉文字 (Speech-to-Text) 和光學字元辨識 (OCR) 的服務模組。
*   **前後端分離**: 基於 Flask 的後端 API 和原生 JavaScript 的前端介面。

---

## 前置條件
- Python 3.10.X
- CUDA 
- ffmpeg
- Tesseract OCR
- Ollama 
- CWA API Key
- Visual Studio 的 C++ Desktop Development Tools
- Java

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 設定api_key
-.env
CWA_API_KEY=your_cwa_api_key_here

## 使用方法
步驟 1：建立靜態知識庫
這是運行專案前的必要準備工作。

放置知識文件
將您希望納入知識庫的所有文件（如 .pdf、.txt、.docx 等），放置於 rag_system/documents/ 資料夾中。

執行建立腳本
在終端機運行以下命令：

bash
python rag_system/scripts/build_static_db.py
此命令會將上述文件轉換為向量資料庫。每當知識文件有變動時，需重新執行本步驟。

步驟 2：獲取天氣並建立動態知識庫（首次運行）
獲取最新天氣
天氣資訊會寫入 data/weather_for_llm.txt，執行下列命令：

bash
python backend/weather_scheduler.py update
建立動態知識庫
將天氣資料轉換為動態知識庫：

bash
python rag_system/scripts/build_rag_db.py
**提示：**在生產環境下，建議讓 weather_scheduler.py 在背景持續運行，並定期調用 build_rag_db.py 來維護最新動態知識。

步驟 3：啟動後端 Flask 服務
在終端機執行：

bash
python backend/app.py
預設服務將運行於 http://localhost:8081。

步驟 4：啟動前端介面
切換目錄

bash
cd frontend
啟動簡易伺服器

bash
python -m http.server 8080
前端服務預設於 http://localhost:8080 運行。

訪問應用

打開瀏覽器前往 http://localhost:8080

開始使用您的應用！

📄 檔案說明
如需了解各檔案的詳細功能、用途或可自訂的設定，請參閱專案根目錄下的 FileDescription.md 文件。

注意事項
上述指令如需運用於生產環境或自動化，可整合至 shell 腳本或 CI/CD 流程中。

部分指令涉及程式碼執行，請務必確認內容安全且來源可信。
