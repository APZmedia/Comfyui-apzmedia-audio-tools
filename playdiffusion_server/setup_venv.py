#!/usr/bin/env python3
"""
Setup script for PlayDiffusion isolated environment

Creates a venv, installs PlayDiffusion and its dependencies,
and prepares the server for use.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_cmd(cmd, cwd=None, timeout=300):
    """Run a command and return success status."""
    print(f"[Setup] Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            print(f"[Setup] Error: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"[Setup] Timeout after {timeout}s")
        return False
    except Exception as e:
        print(f"[Setup] Exception: {e}")
        return False


def create_venv(venv_path):
    """Create a Python virtual environment."""
    if Path(venv_path, "Scripts", "python.exe").exists():
        print(f"[Setup] Venv already exists at {venv_path}")
        return True

    print(f"[Setup] Creating venv at {venv_path}...")
    return run_cmd([sys.executable, "-m", "venv", venv_path])


def get_venv_python(venv_path):
    """Get path to Python executable in venv."""
    if sys.platform == "win32":
        return str(Path(venv_path) / "Scripts" / "python.exe")
    else:
        return str(Path(venv_path) / "bin" / "python")


def install_packages(venv_path):
    """Install PlayDiffusion and server dependencies."""
    python = get_venv_python(venv_path)

    # Upgrade pip first
    print("[Setup] Upgrading pip...")
    if not run_cmd([python, "-m", "pip", "install", "--upgrade", "pip"]):
        return False

    # Install requirements
    print("[Setup] Installing requirements...")
    req_file = Path(__file__).parent / "requirements.txt"
    if not run_cmd([python, "-m", "pip", "install", "-r", str(req_file)], timeout=600):
        print("[Setup] Failed to install requirements")
        return False

    return True


def create_launcher(venv_path, models_dir):
    """Create a launcher script for the server."""
    python = get_venv_python(venv_path)
    server_script = Path(__file__).parent / "server.py"

    if sys.platform == "win32":
        launcher_content = f'''@echo off
echo [Launcher] Starting PlayDiffusion Server...
call "{venv_path}\\Scripts\\activate.bat"
python "{server_script}" --models-dir "{models_dir}"
'''
        launcher_path = Path(__file__).parent / "launch_server.bat"
    else:
        launcher_content = f'''#!/bin/bash
echo "[Launcher] Starting PlayDiffusion Server..."
source "{venv_path}/bin/activate"
python "{server_script}" --models-dir "{models_dir}"
'''
        launcher_path = Path(__file__).parent / "launch_server.sh"

    launcher_path.write_text(launcher_content)
    if sys.platform != "win32":
        launcher_path.chmod(0o755)

    print(f"[Setup] Created launcher: {launcher_path}")
    return str(launcher_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--venv-path", default=None, help="Path to create venv")
    parser.add_argument("--models-dir", default=None, help="Path for model cache")
    args = parser.parse_args()

    # Default paths
    if args.venv_path is None:
        venv_path = Path(__file__).parent / "venv"
    else:
        venv_path = Path(args.venv_path)

    if args.models_dir is None:
        # Default to ComfyUI models/playdiffusion
        models_dir = Path(__file__).parent.parent / "models" / "playdiffusion"
    else:
        models_dir = Path(args.models_dir)

    models_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PlayDiffusion Server Setup")
    print("=" * 60)
    print(f"Venv path: {venv_path}")
    print(f"Models dir: {models_dir}")
    print()

    # Step 1: Create venv
    if not create_venv(str(venv_path)):
        print("[Setup] FAILED: Could not create venv")
        return 1

    # Step 2: Install packages
    if not install_packages(str(venv_path)):
        print("[Setup] FAILED: Could not install packages")
        return 1

    # Step 3: Create launcher
    launcher = create_launcher(str(venv_path), str(models_dir))

    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("To start the server, run:")
    print(f"  {launcher}")
    print()
    print("Or manually:")
    print(f"  {get_venv_python(venv_path)} {Path(__file__).parent / 'server.py'} --models-dir \"{models_dir}\"")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
