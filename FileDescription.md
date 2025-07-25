### LLM 服務實作指南 (Windows 環境) 

這份指南將引導您在 Windows 環境下，從零開始搭建一個功能完整的 LLM 智能助手服務。它將包含 Ollama 模型整合、RAG (檢索增強生成) 系統、語音轉文字、OCR (光學字元識別)、**台灣氣象資料**自動抓取與整合，以及一個現代化的前端介面。最終，我們將實現一個簡單的 **WordPress 短代碼整合方案(XAMPP)**，讓您可以輕鬆地將服務嵌入到您的 WordPress 網站中。

---

### **1. 環境準備與專案目錄建立**

在開始之前，我們需要準備好開發環境並建立專案所需的目錄結構。這將確保您的專案檔案組織有序，方便後續的管理和開發。

#### **1.1 必要軟體下載與安裝**

請您按照以下連結下載並安裝這些軟體。請務必注意安裝過程中的重要提示！

1.  **Python 3.10.x 
2.  **Ollama
3.  其餘套件在requirements


#### **1.2 專案目錄結構如下**
    ```
    C:\llm_service
    ├── backend
    ├── data
    ├── frontend
    ├── rag_system
    ├── .env 
    ├── main.py
    ├── requirements.txt
    ```
---


### **2. 資料夾功能說明**

#### **2.1 `backend`**

*   **`app.py`**
    *   **功能**: 一個基於 Flask 的後端服務，它負責處理使用者與大型語言模型 (LLM) 的互動。根據使用者查詢內容，決定是啟用靜態知識庫、動態知識庫還是兩者都啟用，以生成更精準的回應，同時還會儲存對話記錄。
    *   **可調整功能**: 可在最後一行設定 `PORT` 號。

*   **`llm_service.py`**
    *   **功能**: 負責接收使用者訊息，整合 RAG 知識庫來增強回答，並透過 Ollama API 處理使用者與 LLM 的互動。
    *   **可調整功能**:
        1.  `class LLMService`:
            *   `ollama_url: str = "http://localhost:11434"`  *(<-- 這裡設定 Ollama 服務 URL，11434 為預設)*
            *   `model_name: str = "llama3.1:8b"`             *(<-- 這裡設定要使用的模型名稱)*
        2.  `call_ollama` 中的 `options` 參數:
            ```json
            "options": { 
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 50
            } 
            ```
        3.  `generate_response` 中的提示 (Prompt):
            *   可分別設定執行 RAG 時與不執行 RAG 時的系統提示。

*   **`multimedia_service.py` (暫時沒用到)**
    *   **功能**: 它主要提供語音轉文字和 OCR 功能，使用者可以透過此服務，將音頻轉換為文字，或從圖片中提取文字。

*   **`ocr_service.py` (暫時沒用到)**
    *   **功能**: 它主要做 OCR 功能，從圖片中提取文字。

*   **`speech_to_text.py` (暫時沒用到)**
    *   **功能**: 它負責將音頻轉換為文字。

*   **`test_api.py` (目前只有基礎功能測試)**
    *   **功能**: 測試 `app.py`。

*   **`weather_scheduler.py`**
    *   **功能**: 自動獲取台灣的天氣預報和即時觀測數據，並將其整理成一個 LLM 可以讀懂的摘要文件 (`weather_for_llm.txt`)，以便後續的 RAG 系統使用。

*   **`weather_service.py`**
    *   **功能**: 它的主要功能是從台灣中央氣象署 (CWA) 的開放數據 API 獲取天氣資訊。

> ##### **自訂天氣地點設定流程**
>
> ###### **步驟 1：確定您想監控的地點**
>
> 1.  **列出「預報地區」**: 確定您想要天氣預報的縣市名稱 (例如：`臺北市`, `高雄市`, `彰化縣`)。
> 2.  **查找對應的「觀測站名稱」**: 查詢 CWA API 數據，找出上述每個「預報地區」最適合代表其即時天氣的「觀測站名稱」(例如：`臺北`, `高雄`, `彰化`)。
>
> ###### **步驟 2：修改 `weather_service.py`**
>
> 1.  **檔案位置**: `C:\llm_service\backend\weather_service.py`
> 2.  **目標**: 更新 `TaiwanWeatherService` 類別以查詢您指定的「預報地區」。
> 3.  **操作**:
>     *   在 `TaiwanWeatherService` 類別的 `__init__` 方法中，找到 `self.LOCATIONS_TO_QUERY`。
>     *   將該列表更新為您在步驟 1 中確定的「預報地區」列表。
>
> **範例修改**:
> ```python
> # 原始
> # self.LOCATIONS_TO_QUERY = ['臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市', '基隆市', '屏東縣']
> # 修改後 (假設您想查詢 臺北, 高雄, 彰化)
> self.LOCATIONS_TO_QUERY = ['臺北市', '高雄市', '彰化縣']
> ```
> ---
> ###### **步驟 3：修改 `weather_scheduler.py`**
>
> 1.  **檔案位置**: `C:\llm_service\backend\weather_scheduler.py`
> 2.  **目標**: 配置排程器以使用您指定的地點，並建立預報地區與觀測站的對應關係。
> 3.  **操作**:
>     *   **修改 `self.LOCATIONS_TO_QUERY`**:
>         *   在 `WeatherScheduler` 類別的 `__init__` 方法中，將此列表修改為與 `weather_service.py` 中**完全一致**的「預報地區」列表。
>         *   **範例 (與 `weather_service.py` 保持一致)**:
>             ```python
>             # 原始
>             # self.LOCATIONS_TO_QUERY = ['臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市', '基隆市', '屏東縣']
>             # 修改後
>             self.LOCATIONS_TO_QUERY = ['臺北市', '高雄市', '彰化縣']
>             ```
>     *   **修改 `self.location_to_station_map`**:
>         *   **位置**: 在 `WeatherScheduler` 類別的 `__init__` 方法中。
>         *   **操作**:
>             *   刪除不再需要的地區與觀測站的映射。
>             *   新增您在步驟 1 中確定的「預報地區」到「觀測站名稱」的對應關係。
>         *   **範例 (根據上述目標地點)**:
>             ```python
>             # 原始
>             # self.location_to_station_map = {
>             #     '臺北市': '臺北', '新北市': '新北', '桃園市': '新屋', '臺中市': '臺中',
>             #     '臺南市': '臺南', '高雄市': '高雄', '基隆市': '基隆', '屏東縣': '屏東'
>             # }
>             # 修改後
>             self.location_to_station_map = {
>                 '臺北市': '臺北',    # 預報地區「臺北市」對應觀測站「臺北」
>                 '高雄市': '高雄',    # 預報地區「高雄市」對應觀測站「高雄」
>                 '彰化縣': '彰化'     # 預報地區「彰化縣」對應觀測站「彰化」
>             }
>             ```

---

#### **2.2 `data`**

*   **功能**: 儲存資料。

---

#### **2.3 `frontend`**

##### **專案結構與檔案功能說明**

###### **根目錄 (`C:\llm_service\frontend`)**

*   **`test_server.py`**:
    *   **功能**: 此為測試用的伺服器腳本，用於啟動前端的開發伺服器，方便本地調試。
*   **`測試之前python -m http.server 8080.txt`**:
    *   **功能**: 一個備註文件，記錄了運行簡單 HTTP 伺服器 (用於提供靜態文件) 的命令 `python -m http.server 8080` 及其執行前的注意事項。

---

###### **`static` 資料夾**

此資料夾用於存放前端應用所需的靜態資源。

*   **`static/css/style.css`**:
    *   **功能**: 包含所有 CSS 樣式規則，定義網頁的視覺外觀、佈局與風格。
*   **`static/js/` 資料夾**:
    *   `app.js`: 作為前端應用程式的主要 JavaScript 入口文件，負責初始化應用、路由管理等核心邏輯。
    *   `chat.js`: 處理聊天功能的 JavaScript 邏輯，包括消息發送、接收與顯示。
    *   `documents.js`: 處理與文檔相關的 JavaScript 邏輯，可能用於展示文檔列表、內容或搜索。
    *   `ocr.js`: 處理 OCR 功能的 JavaScript 邏輯，負責圖片上傳、調用後端 OCR 服務及顯示結果。
    *   `utils.js`: 存放常用的 JavaScript 工具函數，供其他 JS 文件重複使用。
    *   `voice.js`: 處理語音相關功能的 JavaScript 邏輯，可能用於音頻錄製、調用後端語音轉文字服務。
    *   `weather.js`: 處理天氣查詢功能的 JavaScript 邏輯，負責調用後端天氣 API 並顯示天氣資訊。
*   **`static/locales/` 資料夾**:
    *   `en.json`: 存放英文的本地化 (Internationalization) 文本資源。
    *   `zh-CN.json`: 存放簡體中文的本地化文本資源。
    *   `zh-TW.json`: 存放繁體中文的本地化文本資源。

---

###### **`templates` 資料夾**

此資料夾通常用於存放前端應用所需的 HTML 模板文件。

*   **`templates/index.html`**:
    *   **功能**: 作為應用程式的主 HTML 文件，是使用者訪問時載入的首頁，包含引入 CSS 和 JavaScript 文件的鏈接。

---

### **2.4 RAG 系統腳本功能說明 (`rag_system`)**

本文檔旨在說明 `rag_system` 資料夾下各個腳本的功能與可自訂的設定，以便清晰地了解 RAG (檢索增強生成) 系統的資料庫建立與服務流程。

---

#### **`vector_store.py`**

*   **功能**:
    *   定義了 `VectorStoreManager` 類別，是整個 RAG 系統的基石，負責管理向量資料庫。
    *   封裝了與 ChromaDB 向量資料庫的互動，包括初始化、新增文件、以及執行相似度搜索。
    *   負責將文字資料透過 HuggingFace 的嵌入模型轉換為向量。
*   **主要可自訂的設定**:
    1.  **嵌入模型**:
        *   **位置**: `VectorStoreManager` 類別的 `__init__` 方法中的 `embedding_model` 參數。
        *   **說明**: 可更換為 HuggingFace 上其他支援 `sentence-transformers` 的嵌入模型。
    2.  **相似度搜索參數**:
        *   **位置**: `get_relevant_context` 方法中的 `k` 和 `max_length` 參數。
        *   **說明**: 可調整以改變檢索結果的數量和內容長度。
    3.  **文件批次處理**:
        *   **位置**: `add_documents` 方法中的 `batch_size` 參數。
        *   **說明**: 可調整每批次處理的文件數量，以在記憶體消耗和處理速度之間取得平衡。

---

#### **`document_loader.py`**

*   **功能**:
    *   定義了 `DocumentLoader` 類別，負責從檔案系統中讀取不同格式的文件。
    *   支援 `.pdf`, `.txt`, `.docx`, `.json` 等多種格式，並將其內容轉換為 LangChain 的 `Document` 物件。
    *   使用 `RecursiveCharacterTextSplitter` 將長文檔切分為較小的片段。
*   **主要可自訂的設定**:
    1.  **文字切割器參數**:
        *   **位置**: `DocumentLoader` 類別的 `__init__` 方法中 `text_splitter` 的 `chunk_size` 和 `chunk_overlap` 參數。
        *   **說明**: 可調整以改變文檔的切割方式。
    2.  **支援的檔案格式**:
        *   **位置**: `__init__` 方法中的 `self.supported_extensions` 字典。
        *   **說明**: 可透過新增或修改此字典，來擴展支援的檔案類型。
    3.  **JSON 轉文字邏輯**:
        *   **位置**: `_json_to_text` 方法。
        *   **說明**: 可修改此方法的邏輯，以自訂如何將複雜的 JSON 結構轉換為純文字。

---

#### **`build_static_db.py`**

*   **功能**:
    *   一個專門用於建立或重建「靜態」知識庫的腳本。
    *   它會刪除舊的 `static_db`，然後讀取 `rag_system/documents` 目錄下的所有支援文件，將其轉換為向量並存入新的 `static_db`。
    *   設計為手動執行，用於更新不常變動的核心知識。
*   **主要可自訂的設定**:
    1.  **來源與目標目錄**:
        *   **位置**: 程式碼開頭的 `STATIC_DOCS_DIR` 和 `STATIC_DB_DIR` 變數。
        *   **說明**: 可修改以指定不同的靜態文件來源目錄和向量資料庫儲存目錄。

---

#### **`build_rag_db.py`**

*   **功能**:
    *   一個專門用於建立或重建「動態」知識庫的腳本。
    *   它會刪除舊的 `dynamic_db`，然後讀取 `data` 目錄下的 `weather_for_llm.txt` 文件，將其轉換為向量并存入新的 `dynamic_db`。
    *   設計為由排程器（如 `weather_scheduler.py`）自動調用。
*   **主要可自訂的設定**:
    1.  **來源與目標目錄**:
        *   **位置**: 程式碼開頭的 `DYNAMIC_DATA_DIR` 和 `DYNAMIC_DB_DIR` 變數。
    2.  **處理的文件模式**:
        *   **位置**: `build_dynamic_database` 函數中 `loader.load_all_documents` 的 `file_pattern` 參數。
        *   **說明**: 可修改 `file_pattern` 來處理不同的檔案名稱或模式。

---

#### **`build_dbs.py`**

*   **功能**:
    *   一個通用的腳本，可以一次性建立或重建「靜態」和「動態」兩個知識庫。
*   **主要可自訂的設定**:
    1.  **檔案處理模式**:
        *   **位置**: `main` 函數中調用 `build_database` 時傳入的 `file_pattern` 參數。
    2.  **目錄配置**:
        *   **位置**: 程式碼開頭的 `STATIC_DOCS_DIR`, `DYNAMIC_DATA_DIR`, `STATIC_DB_DIR`, `DYNAMIC_DB_DIR` 變數。

---

#### **`rag_service.py`**

*   **功能**:
    *   定義了 `RAGService` 類別，是後端應用 (如 `llm_service.py`) 調用 RAG 功能的統一入口。
    *   在初始化時，同時載入「靜態」和「動態」兩個向量資料庫。
    *   提供一個 `query` 方法，可以根據傳入的參數，靈活地決定是查詢靜態庫、動態庫，還是兩者都查。
*   **主要可自訂的設定**:
    1.  **查詢邏輯**:
        *   **位置**: `query` 方法中的 `k`, `use_static`, `use_dynamic` 參數。
    2.  **上下文組合方式**:
        *   **位置**: `query` 方法中組合 `all_context_parts` 的部分。
        *   **說明**: 可修改上下文之間的分隔符或為不同來源的上下文添加標題。

---

#### **`test_rag_service.py`**

*   **功能**:
    *   一個用於測試 `RAGService` 是否正常運作的腳本。
    *   其設計目的是測試知識庫的初始化、重建，以及對靜態、動態和聯合查詢的驗證。
*   **重要提示**:
    *   您提供的 `test_rag_service.py` 腳本中調用了 `rag_service.rebuild_static_db()` 和 `rag_service.rebuild_dynamic_db()` 方法。
    *   然而，在您描述的架構中，這些重建功能已被獨立為 `build_static_db.py` 和 `build_rag_db.py` 腳本。
    *   因此，若要運行此測試腳本，需要將其修改為**直接執行 `build_static_db.py` 和 `build_rag_db.py`**，而不是調用 `rag_service` 內部的方法。