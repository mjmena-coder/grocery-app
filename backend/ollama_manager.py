import subprocess
import time
import requests

OLLAMA_HOST = "http://127.0.0.1:11434"
STARTUP_TIMEOUT_SECONDS = 15


def is_ollama_running() -> bool:
    try:
        return requests.get(f"{OLLAMA_HOST}/api/tags", timeout=1).status_code == 200
    except requests.exceptions.RequestException:
        return False


def ensure_ollama_running() -> None:
    if is_ollama_running():
        return
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.time() + STARTUP_TIMEOUT_SECONDS
    while time.time() < deadline:
        if is_ollama_running():
            return
        time.sleep(0.5)
    raise RuntimeError("Ollama did not start within timeout")