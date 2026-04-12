import contextlib
import os

import torch

from .play_diffusion_utils import _ensure_playdiffusion_installed

# Module-level cache — avoids reloading the ~10 GB model between executions.
_MODEL_CACHE: dict = {}


def _playdiffusion_models_dir() -> str:
    """Return the ComfyUI models/playdiffusion/ directory, creating it if needed."""
    try:
        import folder_paths
        path = os.path.join(folder_paths.models_dir, "playdiffusion")
    except ImportError:
        # Fallback: place next to this file's package root
        path = os.path.join(os.path.dirname(__file__), "..", "models", "playdiffusion")

    os.makedirs(path, exist_ok=True)
    return os.path.abspath(path)


@contextlib.contextmanager
def _hf_cache_in(directory: str):
    """Temporarily redirect HuggingFace Hub downloads to *directory*.

    PlayDiffusion calls hf_hub_download() internally; pointing HF_HUB_CACHE at
    our ComfyUI models folder makes those weights land there instead of
    ~/.cache/huggingface/hub.
    """
    old = os.environ.get("HF_HUB_CACHE")
    os.environ["HF_HUB_CACHE"] = directory
    try:
        yield
    finally:
        if old is not None:
            os.environ["HF_HUB_CACHE"] = old
        else:
            os.environ.pop("HF_HUB_CACHE", None)


class PlayDiffusionLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "device": (["cuda", "cpu"],),
            }
        }

    RETURN_TYPES = ("PLAY_DIFFUSION_MODEL",)
    RETURN_NAMES = ("model",)
    FUNCTION = "load_model"
    CATEGORY = "APZmedia/Audio/PlayDiffusion"

    def load_model(self, device):
        if device == "cuda" and not torch.cuda.is_available():
            print("[APZmedia] CUDA not available — falling back to CPU")
            device = "cpu"

        if device not in _MODEL_CACHE:
            _ensure_playdiffusion_installed()
            from playdiffusion import PlayDiffusion

            models_dir = _playdiffusion_models_dir()
            print(f"[APZmedia] PlayDiffusion model directory: {models_dir}")
            print(f"[APZmedia] Loading PlayDiffusion on {device} "
                  "(downloading model weights on first run — ~10 GB) ...")

            with _hf_cache_in(models_dir):
                _MODEL_CACHE[device] = PlayDiffusion(device=device)

            print("[APZmedia] PlayDiffusion ready.")

        return (_MODEL_CACHE[device],)
