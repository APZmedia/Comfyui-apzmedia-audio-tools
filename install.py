"""
ComfyUI Manager install script — runs once when the custom node is installed
or updated via ComfyUI Manager.

Pip dependencies are handled by requirements.txt (ComfyUI Manager reads that
file and calls pip automatically).  This script handles anything that pip
alone cannot do: creating model directories and printing first-run guidance.
"""

import os
import sys


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


def _check_pip_packages():
    """Verify that required packages are importable; warn if not."""
    missing = []

    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        missing.append("faster-whisper")

    try:
        import playdiffusion  # noqa: F401
    except ImportError:
        missing.append("git+https://github.com/playht/PlayDiffusion.git")

    if missing:
        print("[APZmedia] The following packages are not yet installed "
              "and will be downloaded on first use:")
        for pkg in missing:
            print(f"  pip install {pkg}")


if __name__ == "__main__":
    print("[APZmedia] Running install script …")
    _ensure_model_dirs()
    _check_pip_packages()
    print("[APZmedia] Install complete.")
