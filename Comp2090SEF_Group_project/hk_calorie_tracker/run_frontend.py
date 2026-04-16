from __future__ import annotations

import os
import signal
import socket
import sys
import subprocess
import time
from pathlib import Path


def maybe_reexec_with_local_venv() -> None:
    script_dir = Path(__file__).resolve().parent
    if os.name == "nt":
        local_python = script_dir / ".venv" / "Scripts" / "python.exe"
    else:
        local_python = script_dir / ".venv" / "bin" / "python"

    current_python = Path(sys.executable).resolve()
    if local_python.exists() and local_python.resolve() != current_python:
        os.execv(str(local_python), [str(local_python), str(Path(__file__).resolve()), *sys.argv[1:]])


def _port_open(host: str, port: int) -> bool:
    """Return True if something is already listening on the given port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


def _read_backend_port(script_dir: Path) -> int:
    port_file = script_dir / "api_port.txt"
    try:
        return int(port_file.read_text().strip())
    except Exception:
        return 5050


def start_backend_if_needed(script_dir: Path) -> subprocess.Popen | None:
    """Start the Flask backend as a background process if it isn't already running."""
    port = _read_backend_port(script_dir)
    if _port_open("127.0.0.1", port):
        print(f"[frontend] Backend already running on port {port}.", flush=True)
        return None

    print("[frontend] Starting backend…", flush=True)
    backend_script = script_dir / "run_backend.py"
    # On Windows use CREATE_NEW_PROCESS_GROUP so the child survives the parent
    kwargs: dict = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen(
        [sys.executable, str(backend_script)],
        cwd=str(script_dir),
        **kwargs,
    )

    # Wait up to 15 s for the backend to become reachable
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        # Re-read port each iteration in case run_backend chose a different one
        port = _read_backend_port(script_dir)
        if _port_open("127.0.0.1", port):
            print(f"[frontend] Backend ready on port {port}.", flush=True)
            return proc
        time.sleep(0.4)

    print("[frontend] WARNING: backend did not become ready in time — continuing anyway.", flush=True)
    return proc


def main() -> None:
    maybe_reexec_with_local_venv()
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)

    backend_proc = start_backend_if_needed(script_dir)

    streamlit_app = script_dir / "streamlit_app.py"
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(streamlit_app), *sys.argv[1:]],
            check=False,
        )
    finally:
        # If we started the backend ourselves, shut it down when Streamlit exits
        if backend_proc is not None and backend_proc.poll() is None:
            print("[frontend] Stopping backend…", flush=True)
            if os.name == "nt":
                backend_proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                backend_proc.terminate()
            try:
                backend_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_proc.kill()


if __name__ == "__main__":
    main()