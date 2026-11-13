"""Web application launcher module for Datheon Autonomous AI Agent."""

import subprocess
import sys
from pathlib import Path


def launch_web_ui(port: int = 8501, host: str = "localhost") -> None:
    """Launch the Streamlit web application as a subprocess."""
    web_app_path = Path(__file__).resolve().parent.parent / "web_app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(web_app_path),
        "--server.port",
        str(port),
        "--server.address",
        host,
        "--browser.gatherUsageStats",
        "false",
    ]
    print(f"Launching Datheon Autonomous Agent Web UI at http://{host}:{port} ...")
    subprocess.run(cmd)


if __name__ == "__main__":
    launch_web_ui()
