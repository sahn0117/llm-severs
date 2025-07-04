@echo off
title 自动更新动态RAG知识库

REM --- 1. 定義您的環境路徑 ---
SET PROJECT_ROOT=%~dp0
SET VENV_ACTIVATE_CMD=%PROJECT_ROOT%venv\Scripts\activate.bat
SET BACKEND_DIR=%PROJECT_ROOT%backend
SET RAG_SCRIPTS_DIR=%PROJECT_ROOT%rag_system\scripts

echo.
echo ==================================================
echo        啟動動態RAG知識庫自動更新流程
echo ==================================================
echo.

REM --- 2. 啟用 Python 虛擬環境 ---
echo 正在啟用 Python 虛擬環境...
CALL "%VENV_ACTIVATE_CMD%"
IF %ERRORLEVEL% NEQ 0 (
    echo 錯誤：無法啟用虛擬環境。請檢查路徑：%VENV_ACTIVATE_CMD%
    pause
    EXIT /B 1
)
echo.

REM --- 3. 執行天氣資料抓取 (生成 weather_for_llm.txt) ---
echo 正在抓取最新天氣資料並生成摘要檔案...
CD /D %BACKEND_DIR%
python weather_scheduler.py update
IF %ERRORLEVEL% NEQ 0 (
    echo 錯誤：天氣資料抓取失敗。請檢查 weather_scheduler.py 的日誌。
    pause
    EXIT /B 1
)
echo.

REM --- 4. 觸發動態 RAG 知識庫重建 ---
echo 正在觸發動態 RAG 知識庫重建 (build_dbs.py dynamic)...
CD /D %RAG_SCRIPTS_DIR%
python build_dbs.py dynamic
IF %ERRORLEVEL% NEQ 0 (
    echo 錯誤：動態 RAG 知識庫重建失敗。請檢查 build_dbs.py 的日誌。
    pause
    EXIT /B 1
)
echo.

echo ==================================================
echo        動態RAG知識庫更新流程完成！
echo ==================================================
echo.
pause