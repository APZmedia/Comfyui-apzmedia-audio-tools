import json
import re


class WordReplacer:
    """Replace a word or phrase in a transcript and locate its time region.

    Feed the output directly into PlayDiffusionInpaint and AudioRegionSelector.
    Handles multi-word phrases and is case-insensitive.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "transcript": ("STRING", {
                    "multiline": True,
                    "tooltip": "Full transcript from AudioTranscribe",
                }),
                "word_times_json": ("STRING", {
                    "multiline": True,
                    "default": "[]",
                    "tooltip": "Word timestamps JSON from AudioTranscribe",
                }),
                "original_phrase": ("STRING", {
                    "default": "Neo",
                    "tooltip": "Word or phrase to replace (case-insensitive)",
                }),
                "replacement_phrase": ("STRING", {
                    "default": "Trinity",
                    "tooltip": "Replacement word or phrase",
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "FLOAT", "FLOAT")
    RETURN_NAMES = (
        "input_text",
        "output_text",
        "word_times_json",
        "region_start_ms",
        "region_end_ms",
    )
    FUNCTION = "replace_word"
    CATEGORY = "APZmedia/Audio/PlayDiffusion"

    def replace_word(self, transcript, word_times_json, original_phrase, replacement_phrase):
        word_times = json.loads(word_times_json) if word_times_json.strip() else []

        # Build output_text with case-insensitive whole-word substitution
        pattern = re.compile(r"\b" + re.escape(original_phrase) + r"\b", re.IGNORECASE)
        output_text = pattern.sub(replacement_phrase, transcript)

        # Locate time region for the replaced phrase in the word timestamps
        orig_words = original_phrase.lower().split()
        region_start_ms = 0.0
        region_end_ms = 0.0

        if word_times and orig_words:
            # Strip punctuation for comparison
            def normalize(s):
                return s.strip().lower().strip(".,!?;:\"'")

            normalized = [normalize(w["word"]) for w in word_times]

            n = len(orig_words)
            found = False
            for i in range(len(normalized) - n + 1):
                if normalized[i: i + n] == orig_words:
                    region_start_ms = word_times[i]["start"] * 1000.0
                    region_end_ms = word_times[i + n - 1]["end"] * 1000.0
                    found = True
                    break

            if not found:
                print(f"[APZmedia WordReplacer] Phrase '{original_phrase}' "
                      "not found in word timestamps — region will be 0ms/0ms")

        return (transcript, output_text, word_times_json, region_start_ms, region_end_ms)
