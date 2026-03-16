import subprocess
import sys
import os

def run():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(base_dir, "main.py")

    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            main_file,
            "--server.headless=true",
            "--browser.serverAddress=localhost"
        ]
    )

if __name__ == "__main__":
    run()
