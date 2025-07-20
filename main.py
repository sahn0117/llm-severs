# C:\llm_service\main.py
# 版本: v3.3 - 1小時正式服務版

import subprocess
import sys
import os
import time
import shutil
import atexit
from pathlib import Path
from datetime import datetime, timedelta
import platform
import signal

# --- 全域變數，用於追蹤子程序 ---
flask_process = None

def cleanup():
    """註冊一個退出函數，確保 main.py 關閉時，Flask 服務也會被徹底關閉"""
    global flask_process
    if flask_process and flask_process.poll() is None:
        print("\n偵測到主程序退出，正在關閉 Flask 服務...")
        try:
            if platform.system() == "Windows":
                flask_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                flask_process.terminate()
            flask_process.wait(timeout=5)
            print("Flask 服務已成功關閉。")
        except subprocess.TimeoutExpired:
            print("關閉 Flask 服務超時，將強制終止。")
            flask_process.kill()
        except Exception as e:
            print(f"關閉 Flask 服務時發生錯誤: {e}")
atexit.register(cleanup)


def print_header(title):
    """印出帶有標題的分隔線"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def run_step(command, step_name, working_dir, is_background=False):
    """執行一個流程步驟，可選擇在背景執行"""
    global flask_process
    print(f"\n>>> [STEP] 開始執行: {step_name}")
    print(f"    - 工作目錄: {working_dir}")
    print(f"    - 指令: {' '.join(command)}")
    
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        if is_background:
            creationflags = 0
            if platform.system() == "Windows":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            
            process = subprocess.Popen(command, cwd=working_dir, env=env, creationflags=creationflags)
            flask_process = process
            print(f"[OK] {step_name} 已在背景啟動，程序 ID: {process.pid}")
            return process
        else:
            result = subprocess.run(
                command, check=True, capture_output=True, text=True, 
                encoding='utf-8', errors='replace', env=env, cwd=working_dir
            )
            if result.stdout: print(result.stdout)
            print(f"[OK] {step_name} ... 成功完成！")
            return True
    except Exception as e:
        print(f"\n[FATAL ERROR] {step_name} ... 執行失敗！")
        error_output = e.stderr if hasattr(e, 'stderr') else str(e)
        print("-" * 20 + " [ 錯誤詳情 ] " + "-" * 20)
        print(error_output)
        return None

def run_full_cycle():
    """執行一次完整的重啟與更新循環"""
    global flask_process
    print_header(f"開始新一輪的更新與重啟循環 @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if flask_process and flask_process.poll() is None:
        print("\n>>> [STEP] 正在關閉現有的 Flask 服務...")
        if platform.system() == "Windows":
            flask_process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            flask_process.terminate()
        try:
            flask_process.wait(timeout=5)
            print("[OK] 舊的 Flask 服務已成功關閉。")
        except subprocess.TimeoutExpired:
            print("[WARN] 關閉 Flask 服務超時，將嘗試強制終止。")
            flask_process.kill()
            flask_process.wait()
            print("[OK] Flask 服務已被強制終止。")
        time.sleep(2) 

    PROJECT_ROOT = Path(__file__).parent
    PYTHON_EXECUTABLE = sys.executable
    db_to_delete = PROJECT_ROOT / "rag_system" / "embeddings" / "dynamic_db"

    print(f"\n>>> [STEP] 正在清理舊的動態知識庫...")
    if db_to_delete.exists():
        try:
            shutil.rmtree(db_to_delete)
            print(f"[OK] 目錄已成功刪除。")
        except Exception as e:
            print(f"[FAIL] 刪除目錄時發生嚴重錯誤: {e}")
            return False
    else:
        print("[INFO] 目錄不存在，無需刪除。")

    backend_dir = PROJECT_ROOT / "backend"
    weather_command = [PYTHON_EXECUTABLE, "weather_scheduler.py", "update"]
    if not run_step(weather_command, "抓取最新天氣資料", working_dir=str(backend_dir)): return False

    rag_dir = PROJECT_ROOT / "rag_system" / "scripts"
    rag_command = [PYTHON_EXECUTABLE, "build_dbs.py", "dynamic"]
    if not run_step(rag_command, "重建動態 RAG 知識庫", working_dir=str(rag_dir)): return False

    app_command = [PYTHON_EXECUTABLE, "app.py"]
    run_step(app_command, "啟動 Flask 後端服務", working_dir=str(backend_dir), is_background=True)
    return True

if __name__ == "__main__":
    print_header("動態 RAG 服務守護程序 (v3.3 - 1小時正式版)")
    print(f"--- 使用 Python: {sys.executable}")
    
    run_full_cycle()

    while True:
        # [核心修改] 將時間間隔恢復為一小時
        next_run_time = datetime.now() + timedelta(hours=1)
        print_header("本輪更新完成，API 服務已啟動")
        print(f"下次自動重啟與更新時間約為: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("守護程序將進入一小時休眠... (按 Ctrl+C 可中止守護程序)")
        
        try:
            # [核心修改] 等待 3600 秒 (1 小時)
            time.sleep(3600)
        except KeyboardInterrupt:
            print("\n偵測到 Ctrl+C...")
            sys.exit(0)
            
        run_full_cycle()