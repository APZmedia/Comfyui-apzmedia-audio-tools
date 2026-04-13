"""
PlayDiffusion RVC - HTTP Client Implementation

Transfer speech from a source audio to match a target voice without changing the words.
Communicates with the isolated PlayDiffusion server via HTTP.
"""

import os

from .play_diffusion_utils import audio_to_tempfile, pcm_to_audio_dict


class PlayDiffusionRVC:
    """Transfer speech from a source audio to match a target voice without changing the words."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("PLAY_DIFFUSION_CLIENT",),
                "source_audio": ("AUDIO",),
                "target_voice": ("AUDIO",),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "voice_conversion"
    CATEGORY = "APZmedia/Audio/PlayDiffusion"

    def voice_conversion(self, client, source_audio, target_voice):
        src_path, _ = audio_to_tempfile(source_audio)
        tgt_path, _ = audio_to_tempfile(target_voice)
        try:
            sample_rate, pcm = client.rvc(
                source_audio_path=src_path,
                target_voice_path=tgt_path,
            )
        finally:
            os.unlink(src_path)
            os.unlink(tgt_path)

        return (pcm_to_audio_dict(sample_rate, pcm),)
