import os
import tempfile

import numpy as np
import torch
import torchaudio


def _ensure_playdiffusion_installed():
    """Check for PlayDiffusion package and raise helpful error if missing."""
    try:
        import playdiffusion  # noqa: F401
        return
    except ImportError as exc:
        raise ImportError(
            "PlayDiffusion package is not installed.\n\n"
            "To install, run this command in your ComfyUI environment:\n"
            "  pip install git+https://github.com/playht/PlayDiffusion.git\n\n"
            "For ComfyUI Portable, use the embedded Python:\n"
            "  C:/AI/ComfyUI_windows_portable/python_embeded/python.exe "
            "-m pip install git+https://github.com/playht/PlayDiffusion.git"
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
