"""
PlayDiffusion HTTP Client

Communicates with the isolated PlayDiffusion server via HTTP.
Handles server startup, health checks, and API calls.
"""

import os
import json
import tempfile
import subprocess
import time
import sys
from pathlib import Path
from typing import Optional, Tuple, Any

import numpy as np

# Try to import requests, fall back to urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False

# Default server config
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SERVER_STARTUP_TIMEOUT = 300  # 5 minutes for model loading


class PlayDiffusionClient:
    """Client for communicating with PlayDiffusion server."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.base_url = f"http://{host}:{port}"
        self._server_started = False

    def _url(self, endpoint: str) -> str:
        """Build full URL for endpoint."""
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _post(self, endpoint: str, data: dict) -> dict:
        """Make POST request."""
        url = self._url(endpoint)

        if HAS_REQUESTS:
            response = requests.post(url, json=data, timeout=300)
            response.raise_for_status()
            return response.json()
        else:
            # Fallback to urllib
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=300) as response:
                return json.loads(response.read().decode('utf-8'))

    def _get(self, endpoint: str) -> dict:
        """Make GET request."""
        url = self._url(endpoint)

        if HAS_REQUESTS:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        else:
            with urllib.request.urlopen(url, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))

    def health_check(self) -> bool:
        """Check if server is running."""
        try:
            self._get("/health")
            return True
        except Exception:
            return False

    def ensure_server_running(self) -> bool:
        """Start server if not running."""
        if self.health_check():
            return True

        if self._server_started:
            # Already tried to start, something went wrong
            return False

        # Try to start server
        return self._start_server()

    def _start_server(self) -> bool:
        """Start the PlayDiffusion server."""
        # Find server setup
        server_dir = Path(__file__).parent.parent / "playdiffusion_server"
        venv_python = server_dir / "venv" / "Scripts" / "python.exe"
        server_script = server_dir / "server.py"

        if not venv_python.exists():
            raise RuntimeError(
                f"PlayDiffusion server not set up. Run:\n"
                f"  python \"{server_dir / 'setup_venv.py'}\""
            )

        if not server_script.exists():
            raise RuntimeError(f"Server script not found: {server_script}")

        # Get models dir
        try:
            import folder_paths
            models_dir = Path(folder_paths.models_dir) / "playdiffusion"
        except ImportError:
            models_dir = Path(__file__).parent.parent / "models" / "playdiffusion"

        models_dir.mkdir(parents=True, exist_ok=True)

        # Start server process
        print(f"[APZmedia] Starting PlayDiffusion server...")
        cmd = [
            str(venv_python),
            str(server_script),
            "--models-dir", str(models_dir)
        ]

        try:
            # Start and detach
            if sys.platform == "win32":
                subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=str(server_dir)
                )
            else:
                subprocess.Popen(
                    cmd,
                    start_new_session=True,
                    cwd=str(server_dir)
                )

            self._server_started = True

            # Wait for server to be ready
            print("[APZmedia] Waiting for server to start...")
            for i in range(SERVER_STARTUP_TIMEOUT):
                if self.health_check():
                    print("[APZmedia] Server is ready!")
                    return True
                time.sleep(1)

            print("[APZmedia] Server startup timeout")
            return False

        except Exception as e:
            print(f"[APZmedia] Failed to start server: {e}")
            return False

    def tts(self, **kwargs) -> Tuple[int, np.ndarray]:
        """Call TTS endpoint."""
        self.ensure_server_running()

        response = self._post("/tts", kwargs)

        # Parse response
        sample_rate = response["sample_rate"]
        dtype = np.dtype(response["dtype"])
        shape = response["shape"]
        audio = np.frombuffer(response["audio"], dtype=dtype).reshape(shape)

        return sample_rate, audio

    def inpaint(self, **kwargs) -> Tuple[int, np.ndarray]:
        """Call inpaint endpoint."""
        self.ensure_server_running()

        response = self._post("/inpaint", kwargs)

        sample_rate = response["sample_rate"]
        dtype = np.dtype(response["dtype"])
        shape = response["shape"]
        audio = np.frombuffer(response["audio"], dtype=dtype).reshape(shape)

        return sample_rate, audio

    def rvc(self, **kwargs) -> Tuple[int, np.ndarray]:
        """Call RVC endpoint."""
        self.ensure_server_running()

        response = self._post("/rvc", kwargs)

        sample_rate = response["sample_rate"]
        dtype = np.dtype(response["dtype"])
        shape = response["shape"]
        audio = np.frombuffer(response["audio"], dtype=dtype).reshape(shape)

        return sample_rate, audio


# Singleton client instance
_client = None

def get_client() -> PlayDiffusionClient:
    """Get or create the singleton client."""
    global _client
    if _client is None:
        _client = PlayDiffusionClient()
    return _client
