import importlib
import os
import subprocess
import sys
import tempfile

import numpy as np
import torch
import torchaudio

_PLAYDIFFUSION_REPO = "git+https://github.com/playht/PlayDiffusion.git"


def _ensure_playdiffusion_installed():
    """Check for PlayDiffusion package and attempt auto-install if missing."""
    try:
        import playdiffusion  # noqa: F401
        return
    except ImportError:
        pass

    print("[APZmedia] PlayDiffusion package not found. Attempting auto-install...")
    print(f"[APZmedia] Running: pip install {_PLAYDIFFUSION_REPO}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", _PLAYDIFFUSION_REPO],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for large package
        )
        if result.returncode == 0:
            print("[APZmedia] PlayDiffusion installed successfully.")
            # Verify import works after install
            importlib.invalidate_caches()
            try:
                import playdiffusion  # noqa: F401
                return
            except ImportError as exc:
                raise RuntimeError(
                    "Installation appeared to succeed but import still fails. "
                    "Try restarting ComfyUI."
                ) from exc
        else:
            raise RuntimeError(
                f"pip install failed with exit code {result.returncode}.\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Installation timed out after 5 minutes. "
            "PlayDiffusion is a large package (~10 GB). "
            "Try installing manually with:\n"
            f"  pip install {_PLAYDIFFUSION_REPO}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Failed to install PlayDiffusion: {exc}\n"
            f"Install manually with:\n"
            f"  pip install {_PLAYDIFFUSION_REPO}"
        ) from exc


def audio_to_tempfile(audio_dict):
    """Save a ComfyUI AUDIO dict to a temporary WAV file.

    Returns (file_path: str, sample_rate: int).
    Caller is responsible for deleting the file when done.
    """
    waveform = audio_dict["waveform"]
    sample_rate = audio_dict["sample_rate"]

    if waveform.dim() == 3:
        waveform = waveform[0]  # (batch, channels, samples) -> (channels, samples)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    torchaudio.save(tmp.name, waveform.cpu().float(), sample_rate)
    return tmp.name, sample_rate


def pcm_to_audio_dict(sample_rate, pcm_array):
    """Convert PlayDiffusion output (int16 numpy array) to a ComfyUI AUDIO dict.

    Handles both mono (1-D) and multi-channel (2-D: samples x channels) arrays.
    """
    audio_float = pcm_array.astype(np.float32) / 32768.0

    if audio_float.ndim == 1:
        # Mono -> (1, samples)
        audio_float = audio_float[None, :]
    elif audio_float.ndim == 2:
        # (samples, channels) -> (channels, samples)
        audio_float = audio_float.T

    # Add batch dimension: (1, channels, samples)
    tensor = torch.from_numpy(audio_float).unsqueeze(0)
    return {"waveform": tensor, "sample_rate": sample_rate}
