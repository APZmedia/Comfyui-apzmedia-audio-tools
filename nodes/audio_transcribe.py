import json
import os
import tempfile

import torch
import torchaudio

# Module-level cache — Whisper models are large; keep them alive between runs.
_WHISPER_CACHE: dict = {}


def _whisper_models_dir() -> str:
    """Return the ComfyUI models/whisper/ directory, creating it if needed."""
    try:
        import folder_paths
        path = os.path.join(folder_paths.models_dir, "whisper")
    except ImportError:
        path = os.path.join(os.path.dirname(__file__), "..", "models", "whisper")

    os.makedirs(path, exist_ok=True)
    return os.path.abspath(path)


class AudioTranscribe:
    """Transcribe audio with word-level timestamps using a local Whisper model.

    No OpenAI API key required.  Model weights are downloaded automatically to
    ComfyUI's models/whisper/ folder on first use.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "model_size": (["tiny", "base", "small", "medium", "large-v3"],),
            },
            "optional": {
                "language": ("STRING", {
                    "default": "en",
                    "tooltip": (
                        "ISO-639-1 language code (e.g. 'en', 'es'). "
                        "Leave blank for auto-detect."
                    ),
                }),
                "device": (["cuda", "cpu"],),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("transcript", "word_times_json")
    FUNCTION = "transcribe"
    CATEGORY = "APZmedia/Audio/PlayDiffusion"

    def transcribe(self, audio, model_size, language="en", device="cuda"):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ImportError(
                "faster-whisper is not installed.\n"
                "Install it with:  pip install faster-whisper"
            ) from exc

        if device == "cuda" and not torch.cuda.is_available():
            print("[APZmedia] CUDA not available — falling back to CPU for Whisper")
            device = "cpu"

        cache_key = (model_size, device)
        if cache_key not in _WHISPER_CACHE:
            download_root = _whisper_models_dir()
            compute_type = "float16" if device == "cuda" else "int8"
            print(f"[APZmedia] Loading Whisper '{model_size}' on {device} "
                  f"(models → {download_root}) ...")
            _WHISPER_CACHE[cache_key] = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=download_root,
            )

        whisper = _WHISPER_CACHE[cache_key]

        # Save AUDIO to a temp WAV (faster-whisper expects a file path)
        waveform = audio["waveform"]
        sample_rate = audio["sample_rate"]
        if waveform.dim() == 3:
            waveform = waveform[0]

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        torchaudio.save(tmp.name, waveform.cpu().float(), sample_rate)

        try:
            lang = language.strip() or None
            segments, _info = whisper.transcribe(
                tmp.name,
                language=lang,
                word_timestamps=True,
            )

            transcript_parts: list[str] = []
            word_times: list[dict] = []

            for segment in segments:
                text = segment.text.strip()
                if text:
                    transcript_parts.append(text)
                if segment.words:
                    for w in segment.words:
                        word_times.append({
                            "word": w.word.strip(),
                            "start": round(float(w.start), 3),
                            "end": round(float(w.end), 3),
                        })
        finally:
            os.unlink(tmp.name)

        transcript = " ".join(transcript_parts)
        word_times_json = json.dumps(word_times, indent=2)
        return (transcript, word_times_json)
