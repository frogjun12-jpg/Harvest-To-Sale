import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
PID_FILE = ROOT / ".free_servers.json"
PYTHON = Path(sys.executable)

SERVERS = {
    "api": {
        "port": 8000,
        "url": "http://127.0.0.1:8000/health",
        "args": ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        "log": "server_fastapi.free.log",
    },
    "admin": {
        "port": 8501,
        "url": "http://127.0.0.1:8501",
        "args": [
            "-m",
            "streamlit",
            "run",
            "app/ui/streamlit_app.py",
            "--server.address",
            "127.0.0.1",
            "--server.port",
            "8501",
            "--server.headless",
            "true",
        ],
        "log": "server_admin.free.log",
    },
    "shop": {
        "port": 8502,
        "url": "http://127.0.0.1:8502",
        "args": [
            "-m",
            "streamlit",
            "run",
            "app/ui/shop_app.py",
            "--server.address",
            "127.0.0.1",
            "--server.port",
            "8502",
            "--server.headless",
            "true",
        ],
        "log": "server_shop.free.log",
    },
}


def load_pids() -> dict[str, int]:
    if not PID_FILE.exists():
        return {}
    try:
        return json.loads(PID_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_pids(pids: dict[str, int]) -> None:
    PID_FILE.write_text(json.dumps(pids, indent=2), encoding="utf-8")


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def stop_process(pid: int) -> None:
    if not process_alive(pid):
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    for _ in range(20):
        if not process_alive(pid):
            return
        time.sleep(0.2)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass


def check_url(url: str) -> bool:
    try:
        with urlopen(url, timeout=3) as response:
            return 200 <= response.status < 500
    except Exception:
        return False


def env_for_free() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV_FILE": ".env",
            "APP_EDITION": "free",
            "SHOP_EDITION": "free",
            "LLM_PROVIDER": "ollama",
            "EMBEDDING_PROVIDER": "ollama",
            "CHAT_API_URL": "http://localhost:8000/chat",
        }
    )
    return env


def start_servers() -> None:
    pids = load_pids()
    alive = {name: pid for name, pid in pids.items() if process_alive(pid)}
    if alive:
        print(f"already running: {alive}")
        return

    env = env_for_free()
    creationflags = 0
    if os.name == "nt":
        creationflags = (
            subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NO_WINDOW
        )

    started: dict[str, int] = {}
    LOG_DIR.mkdir(exist_ok=True)
    for name, config in SERVERS.items():
        log_path = LOG_DIR / config["log"]
        log_file = log_path.open("a", encoding="utf-8")
        process = subprocess.Popen(
            [str(PYTHON), *config["args"]],
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            close_fds=True,
        )
        started[name] = process.pid
        print(f"started {name}: pid={process.pid}, log={log_path.name}")

    save_pids(started)
    time.sleep(8)
    print_status()


def stop_servers() -> None:
    pids = load_pids()
    for name, pid in pids.items():
        print(f"stopping {name}: pid={pid}")
        stop_process(pid)
    if PID_FILE.exists():
        PID_FILE.unlink()


def print_status() -> None:
    pids = load_pids()
    for name, config in SERVERS.items():
        pid = pids.get(name)
        alive = bool(pid and process_alive(pid))
        url_ok = check_url(config["url"])
        print(f"{name}: pid={pid} alive={alive} url={config['url']} ok={url_ok}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start", "stop", "restart", "status"])
    args = parser.parse_args()

    if args.command == "start":
        start_servers()
    elif args.command == "stop":
        stop_servers()
    elif args.command == "restart":
        stop_servers()
        start_servers()
    elif args.command == "status":
        print_status()


if __name__ == "__main__":
    main()
