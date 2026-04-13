import os

import folder_paths
import torchaudio


class AudioUpload:
    """Load an audio file from ComfyUI's input directory.

    Outputs the decoded AUDIO tensor and the filename stem (no extension),
    which is useful for downstream naming — e.g., saving processed audio
    with the same base name.
    """

    @classmethod
    def INPUT_TYPES(cls):
        audio_files = folder_paths.get_filename_list("audio")
        return {
            "required": {
                "audio": (sorted(audio_files), {"audio_upload": True}),
            }
        }

    RETURN_TYPES = ("AUDIO", "STRING")
    RETURN_NAMES = ("audio", "filename_stem")
    FUNCTION = "load"
    CATEGORY = "APZmedia/Audio"

    def load(self, audio: str):
        audio_path = folder_paths.get_annotated_filepath(audio)

        waveform, sample_rate = torchaudio.load(audio_path)
        # Add batch dimension: (channels, samples) → (1, channels, samples)
        waveform = waveform.unsqueeze(0)

        audio_out = {"waveform": waveform, "sample_rate": sample_rate}

        # Strip any subfolder prefix that ComfyUI may prepend, then remove ext
        basename = os.path.basename(audio)
        stem = os.path.splitext(basename)[0]

        return (audio_out, stem)

    @classmethod
    def IS_CHANGED(cls, audio: str):
        audio_path = folder_paths.get_annotated_filepath(audio)
        try:
            return os.path.getmtime(audio_path)
        except OSError:
            return float("nan")

    @classmethod
    def VALIDATE_INPUTS(cls, audio: str):
        if not folder_paths.exists_annotated_filepath(audio):
            return f"Audio file not found: {audio!r}"
        return True
