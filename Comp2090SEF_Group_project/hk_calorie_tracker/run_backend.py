from __future__ import annotations

import os
import socket
import sys
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


def find_free_port(preferred: int = 5050) -> int:
    """Return preferred port if free, otherwise find the next available one."""
    for port in range(preferred, preferred + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    # Fall back to OS-assigned port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    maybe_reexec_with_local_venv()
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)

    preferred = int(os.environ.get("HK_TRACKER_API_PORT", "5050"))
    port = find_free_port(preferred)

    # Write the port to a file so the frontend can discover it
    port_file = script_dir / "api_port.txt"
    port_file.write_text(str(port))

    from api_server import app

    print(f" * Backend port: {port}", flush=True)
    venv_dir = str(script_dir / ".venv")
    app.run(host="0.0.0.0", port=port, debug=True, exclude_patterns=[venv_dir])


if __name__ == "__main__":
    main()