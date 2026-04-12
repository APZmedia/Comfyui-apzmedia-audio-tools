import os

from .play_diffusion_utils import audio_to_tempfile, pcm_to_audio_dict, _ensure_playdiffusion_installed


class PlayDiffusionTTS:
    """Generate speech from text using a reference voice for speaker cloning."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("PLAY_DIFFUSION_MODEL",),
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

    def tts(self, model, reference_audio, output_text,
            num_steps=16, temperature=1.0, diversity=1.0, guidance=3.0,
            audio_token_syllable_ratio=3.5):
        _ensure_playdiffusion_installed()
        from playdiffusion import TTSInput

        tmp_path, _ = audio_to_tempfile(reference_audio)
        try:
            inp = TTSInput(
                voice=tmp_path,
                output_text=output_text,
                num_steps=num_steps,
                init_temp=temperature,
                init_diversity=diversity,
                guidance=guidance,
                audio_token_syllable_ratio=audio_token_syllable_ratio,
            )
            sample_rate, pcm = model.tts(inp)
        finally:
            os.unlink(tmp_path)

        return (pcm_to_audio_dict(sample_rate, pcm),)
