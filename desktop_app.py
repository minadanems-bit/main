import os
import sys
import time
import socket
import threading
import subprocess

import webview


APP_PORT = 8501
APP_TITLE = "NMS ERP"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900


def wait_for_server(host: str, port: int, timeout: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def run_streamlit():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(base_dir, "main.py")

    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["STREAMLIT_SERVER_HEADLESS"] = "true"

    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            main_file,
            "--server.port",
            str(APP_PORT),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=base_dir,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    threading.Thread(target=run_streamlit, daemon=True).start()

    ok = wait_for_server("127.0.0.1", APP_PORT, timeout=40)
    if not ok:
        raise RuntimeError("Failed to start local Streamlit server.")

    webview.create_window(
        APP_TITLE,
        f"http://127.0.0.1:{APP_PORT}",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(1100, 700),
    )
    webview.start()


if __name__ == "__main__":
    main()
