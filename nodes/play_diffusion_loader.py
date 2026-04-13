"""
PlayDiffusion Loader - HTTP Server Bridge

Ensures the isolated PlayDiffusion server is running.
Returns a client handle that other nodes use to communicate with the server.
"""

from .play_diffusion_client import get_client


class PlayDiffusionLoader:
    """Load/initialize the PlayDiffusion model via isolated server."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "device": (["cuda", "cpu"],),
            }
        }

    RETURN_TYPES = ("PLAY_DIFFUSION_CLIENT",)
    RETURN_NAMES = ("client",)
    FUNCTION = "load_model"
    CATEGORY = "APZmedia/Audio/PlayDiffusion"

    def load_model(self, device):
        client = get_client()

        print(f"[APZmedia] Ensuring PlayDiffusion server is running on {device}...")

        # This will start the server if not running
        if not client.ensure_server_running():
            raise RuntimeError(
                "PlayDiffusion server failed to start.\n"
                "Run setup manually:\n"
                "  python playdiffusion_server/setup_venv.py"
            )

        return (client,)
