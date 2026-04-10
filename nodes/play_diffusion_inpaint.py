import json
import os

from .play_diffusion_utils import audio_to_tempfile, pcm_to_audio_dict


class PlayDiffusionInpaint:
    """Replace words or phrases in existing speech audio using PlayDiffusion.

    Connect AudioTranscribe → WordReplacer → this node for a full word-swap
    pipeline with no full-audio regeneration.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("PLAY_DIFFUSION_MODEL",),
                "audio": ("AUDIO",),
                "input_text": ("STRING", {
                    "multiline": True,
                    "tooltip": "Full original transcript of the audio",
                }),
                "output_text": ("STRING", {
                    "multiline": True,
                    "tooltip": "Edited transcript — change only the word(s) you want to replace",
                }),
                "word_times_json": ("STRING", {
                    "multiline": True,
                    "default": "[]",
                    "tooltip": "Word-level timestamps JSON from the AudioTranscribe node",
                }),
            },
            "optional": {
                "num_steps": ("INT", {
                    "default": 16, "min": 4, "max": 64, "step": 1,
                    "tooltip": "Diffusion denoising steps — more steps = higher quality but slower",
                }),
                "temperature": ("FLOAT", {
                    "default": 1.0, "min": 0.1, "max": 2.0, "step": 0.05,
                    "tooltip": "Sampling temperature",
                }),
                "diversity": ("FLOAT", {
                    "default": 1.0, "min": 0.1, "max": 2.0, "step": 0.05,
                    "tooltip": "Token diversity during sampling",
                }),
                "guidance": ("FLOAT", {
                    "default": 3.0, "min": 0.0, "max": 10.0, "step": 0.1,
                    "tooltip": "Classifier-free guidance scale",
                }),
                "audio_token_syllable_ratio": ("FLOAT", {
                    "default": 3.5, "min": 1.0, "max": 8.0, "step": 0.1,
                    "tooltip": "Audio tokens per syllable — tune if timing feels off",
                }),
            },
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "inpaint"
    CATEGORY = "APZmedia/Audio/PlayDiffusion"

    def inpaint(self, model, audio, input_text, output_text, word_times_json,
                num_steps=16, temperature=1.0, diversity=1.0, guidance=3.0,
                audio_token_syllable_ratio=3.5):
        try:
            from playdiffusion import InpaintInput
        except ImportError as exc:
            raise ImportError(
                "PlayDiffusion package is not installed. "
                "Use the PlayDiffusionLoader node first."
            ) from exc

        word_times = json.loads(word_times_json) if word_times_json.strip() else []

        tmp_path, _ = audio_to_tempfile(audio)
        try:
            inp = InpaintInput(
                audio=tmp_path,
                input_text=input_text,
                output_text=output_text,
                input_word_times=word_times,
                num_steps=num_steps,
                init_temp=temperature,
                init_diversity=diversity,
                guidance=guidance,
                audio_token_syllable_ratio=audio_token_syllable_ratio,
            )
            sample_rate, pcm = model.inpaint(inp)
        finally:
            os.unlink(tmp_path)

        return (pcm_to_audio_dict(sample_rate, pcm),)
