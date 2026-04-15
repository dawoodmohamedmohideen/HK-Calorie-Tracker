from __future__ import annotations

import os
import sys
import subprocess
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


def main() -> None:
    maybe_reexec_with_local_venv()
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    
    streamlit_app = script_dir / "streamlit_app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(streamlit_app), *sys.argv[1:]], check=False)


if __name__ == "__main__":
    main()