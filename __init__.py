from .nodes.speech_length_calculator import SpeechLengthCalculator
from .nodes.audio_waveform_image import AudioWaveformImage

NODE_CLASS_MAPPINGS = {
    "APZ_SpeechLengthCalculator": SpeechLengthCalculator,
    "APZ_AudioWaveformImage": AudioWaveformImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "APZ_SpeechLengthCalculator": "Speech Length Calculator",
    "APZ_AudioWaveformImage": "Audio Waveform Image",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
