import os

from .play_diffusion_utils import audio_to_tempfile, pcm_to_audio_dict


class PlayDiffusionRVC:
    """Transfer speech from a source audio to match a target voice without changing the words."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("PLAY_DIFFUSION_MODEL",),
                "source_audio": ("AUDIO",),
                "target_voice": ("AUDIO",),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "voice_conversion"
    CATEGORY = "APZmedia/Audio/PlayDiffusion"

    def voice_conversion(self, model, source_audio, target_voice):
        try:
            from playdiffusion import RVCInput
        except ImportError as exc:
            raise ImportError(
                "PlayDiffusion package is not installed. "
                "Use the PlayDiffusionLoader node first."
            ) from exc

        src_path, _ = audio_to_tempfile(source_audio)
        tgt_path, _ = audio_to_tempfile(target_voice)
        try:
            inp = RVCInput(
                source_speech=src_path,
                target_voice=tgt_path,
            )
            sample_rate, pcm = model.rvc(inp)
        finally:
            os.unlink(src_path)
            os.unlink(tgt_path)

        return (pcm_to_audio_dict(sample_rate, pcm),)
