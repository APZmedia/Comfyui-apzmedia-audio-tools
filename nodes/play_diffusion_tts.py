"""
PlayDiffusion TTS - HTTP Client Implementation

Generate speech from text using a reference voice for speaker cloning.
Communicates with the isolated PlayDiffusion server via HTTP.
"""

import os

from .play_diffusion_utils import audio_to_tempfile, pcm_to_audio_dict


class PlayDiffusionTTS:
    """Generate speech from text using a reference voice for speaker cloning."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client": ("PLAY_DIFFUSION_CLIENT",),
                "reference_audio": ("AUDIO",),
                "output_text": ("STRING", {
                    "multiline": True,
                    "tooltip": "Text to synthesize in the reference speaker's voice",
                }),
            },
            "optional": {
                "num_steps": ("INT", {
                    "default": 16, "min": 4, "max": 64, "step": 1,
                }),
                "temperature": ("FLOAT", {
                    "default": 1.0, "min": 0.1, "max": 2.0, "step": 0.05,
                }),
                "diversity": ("FLOAT", {
                    "default": 1.0, "min": 0.1, "max": 2.0, "step": 0.05,
                }),
                "guidance": ("FLOAT", {
                    "default": 3.0, "min": 0.0, "max": 10.0, "step": 0.1,
                }),
                "audio_token_syllable_ratio": ("FLOAT", {
                    "default": 3.5, "min": 1.0, "max": 8.0, "step": 0.1,
                }),
            },
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "tts"
    CATEGORY = "APZmedia/Audio/PlayDiffusion"

    def tts(self, client, reference_audio, output_text,
            num_steps=16, temperature=1.0, diversity=1.0, guidance=3.0,
            audio_token_syllable_ratio=3.5):

        tmp_path, _ = audio_to_tempfile(reference_audio)
        try:
            sample_rate, pcm = client.tts(
                reference_audio_path=tmp_path,
                output_text=output_text,
                num_steps=num_steps,
                temperature=temperature,
                diversity=diversity,
                guidance=guidance,
                audio_token_syllable_ratio=audio_token_syllable_ratio,
            )
        finally:
            os.unlink(tmp_path)

        return (pcm_to_audio_dict(sample_rate, pcm),)
