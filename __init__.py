from .nodes.speech_length_calculator import SpeechLengthCalculator
from .nodes.audio_waveform_image import AudioWaveformImage
from .nodes.audio_equalizer import AudioEqualizer

NODE_CLASS_MAPPINGS = {
    "APZ_SpeechLengthCalculator": SpeechLengthCalculator,
    "APZ_AudioWaveformImage": AudioWaveformImage,
    "APZ_AudioEqualizer": AudioEqualizer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "APZ_SpeechLengthCalculator": "Speech Length Calculator",
    "APZ_AudioWaveformImage": "Audio Waveform Image",
    "APZ_AudioEqualizer": "🎚️ Audio Equalizer",
}

# Enable JavaScript extensions
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
