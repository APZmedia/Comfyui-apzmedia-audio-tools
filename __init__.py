import os

# ── Register model sub-directories with ComfyUI ───────────────────────────
try:
    import folder_paths
    for _sub in ("playdiffusion", "whisper"):
        _path = os.path.join(folder_paths.models_dir, _sub)
        os.makedirs(_path, exist_ok=True)
        folder_paths.add_model_folder_path(_sub, _path)
except Exception:
    pass  # folder_paths not available in all ComfyUI builds — safe to ignore
# ──────────────────────────────────────────────────────────────────────────

from .nodes.audio_upload import AudioUpload
from .nodes.speech_length_calculator import SpeechLengthCalculator
from .nodes.audio_waveform_image import AudioWaveformImage
from .nodes.audio_equalizer import AudioEqualizer

# PlayDiffusion — speech inpainting / TTS / voice conversion
from .nodes.play_diffusion_loader import PlayDiffusionLoader
from .nodes.play_diffusion_inpaint import PlayDiffusionInpaint
from .nodes.play_diffusion_tts import PlayDiffusionTTS
from .nodes.play_diffusion_rvc import PlayDiffusionRVC

# PlayDiffusion utilities — transcription, word replacement, region selection
from .nodes.audio_transcribe import AudioTranscribe
from .nodes.word_replacer import WordReplacer
from .nodes.audio_region_selector import AudioRegionSelector

NODE_CLASS_MAPPINGS = {
    "APZ_AudioUpload": AudioUpload,
    "APZ_SpeechLengthCalculator": SpeechLengthCalculator,
    "APZ_AudioWaveformImage": AudioWaveformImage,
    "APZ_AudioEqualizer": AudioEqualizer,
    # PlayDiffusion
    "APZ_PlayDiffusionLoader": PlayDiffusionLoader,
    "APZ_PlayDiffusionInpaint": PlayDiffusionInpaint,
    "APZ_PlayDiffusionTTS": PlayDiffusionTTS,
    "APZ_PlayDiffusionRVC": PlayDiffusionRVC,
    # Utilities
    "APZ_AudioTranscribe": AudioTranscribe,
    "APZ_WordReplacer": WordReplacer,
    "APZ_AudioRegionSelector": AudioRegionSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "APZ_AudioUpload": "Audio Upload",
    "APZ_SpeechLengthCalculator": "Speech Length Calculator",
    "APZ_AudioWaveformImage": "Audio Waveform Image",
    "APZ_AudioEqualizer": "🎚️ Audio Equalizer",
    # PlayDiffusion
    "APZ_PlayDiffusionLoader": "PlayDiffusion Loader",
    "APZ_PlayDiffusionInpaint": "PlayDiffusion Inpaint",
    "APZ_PlayDiffusionTTS": "PlayDiffusion TTS",
    "APZ_PlayDiffusionRVC": "PlayDiffusion Voice Conversion",
    # Utilities
    "APZ_AudioTranscribe": "Audio Transcribe (Whisper)",
    "APZ_WordReplacer": "Word Replacer",
    "APZ_AudioRegionSelector": "Audio Region Selector",
}

# Enable JavaScript extensions
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
