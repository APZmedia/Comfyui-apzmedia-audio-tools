"""
ComfyUI Manager install script — runs once when the custom node is installed
or updated via ComfyUI Manager.

Pip dependencies are handled by requirements.txt (ComfyUI Manager reads that
file and calls pip automatically).  This script handles anything that pip
alone cannot do: creating model directories and printing first-run guidance.
"""

import os
import sys
from pathlib import Path


# Import Path at module level for use in functions
Path = Path


def _ensure_model_dirs():


def _ensure_model_dirs():
    """Create model sub-directories under ComfyUI's models/ folder."""

    # Locate ComfyUI's models/ directory.
    # We walk up from this file until we find a folder that looks like ComfyUI.
    base = os.path.dirname(os.path.abspath(__file__))
    models_dir = None

    # Strategy 1 – folder_paths (already importable if ComfyUI is on sys.path)
    try:
        import folder_paths  # noqa: PLC0415
        models_dir = folder_paths.models_dir
    except ImportError:
        pass

    # Strategy 2 – walk up the tree looking for ComfyUI's characteristic files
    if models_dir is None:
        probe = base
        for _ in range(6):
            probe = os.path.dirname(probe)
            if os.path.isfile(os.path.join(probe, "comfy", "model_management.py")):
                models_dir = os.path.join(probe, "models")
                break

    if models_dir is None:
        print("[APZmedia] Could not locate ComfyUI models/ directory — "
              "model folders will be created on first node execution.")
        return

    for sub in ("playdiffusion", "whisper"):
        path = os.path.join(models_dir, sub)
        os.makedirs(path, exist_ok=True)
        print(f"[APZmedia] Model folder ready: {path}")


def _install_pip_package(package, name=None):
    """Install a pip package using the current Python interpreter."""
    import subprocess  # noqa: PLC0415

    pkg_name = name or package
    print(f"[APZmedia] Installing {pkg_name}...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            timeout=600,  # 10 min timeout for large packages
        )
        if result.returncode == 0:
            print(f"[APZmedia] {pkg_name} installed successfully.")
            return True
        else:
            print(f"[APZmedia] Failed to install {pkg_name}:")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"[APZmedia] Installation timed out ({pkg_name} is large).")
        return False
    except Exception as exc:
        print(f"[APZmedia] Installation error: {exc}")
        return False


def _setup_playdiffusion_server():
    """Set up the isolated PlayDiffusion server venv."""
    import subprocess  # noqa: PLC0415

    server_dir = Path(__file__).parent / "playdiffusion_server"
    setup_script = server_dir / "setup_venv.py"

    if not setup_script.exists():
        print("[APZmedia] PlayDiffusion server setup script not found.")
        return False

    print("[APZmedia] Setting up PlayDiffusion isolated server...")
    print("[APZmedia] This will create a separate Python environment (~10 GB download)...")

    try:
        result = subprocess.run(
            [sys.executable, str(setup_script)],
            capture_output=True,
            text=True,
            timeout=1200,  # 20 min for large downloads
        )
        if result.returncode == 0:
            print("[APZmedia] PlayDiffusion server setup complete!")
            return True
        else:
            print("[APZmedia] Server setup failed:")
            print(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("[APZmedia] Server setup timed out (too slow connection or large download).")
        return False
    except Exception as exc:
        print(f"[APZmedia] Server setup error: {exc}")
        return False


def _check_pip_packages():
    """Set up PlayDiffusion server if needed."""
    import subprocess  # noqa: PLC0415

    # Check for faster-whisper in main env (used for transcription)
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        print("[APZmedia] faster-whisper not found, installing...")
        _install_pip_package("faster-whisper>=1.0.0", "faster-whisper")

    # Check if PlayDiffusion server is set up
    server_dir = Path(__file__).parent / "playdiffusion_server"
    venv_python = server_dir / "venv" / "Scripts" / "python.exe"

    if venv_python.exists():
        print("[APZmedia] PlayDiffusion server is already set up.")
    else:
        print("[APZmedia] PlayDiffusion server not found.")
        _setup_playdiffusion_server()


if __name__ == "__main__":
    print("[APZmedia] Running install script …")
    _ensure_model_dirs()
    _check_pip_packages()
    print("[APZmedia] Install complete.")
