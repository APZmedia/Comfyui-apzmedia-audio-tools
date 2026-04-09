import re
import math


class SpeechLengthCalculator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": 'Enter your script here. "Put spoken words inside quotes!"',
                }),
                "fps": ("INT", {"default": 24, "min": 1, "max": 240, "step": 1}),
                "slow_wpm": ("INT", {"default": 100, "min": 1, "max": 500, "step": 1}),
                "average_wpm": ("INT", {"default": 130, "min": 1, "max": 500, "step": 1}),
                "fast_wpm": ("INT", {"default": 160, "min": 1, "max": 500, "step": 1}),
                "additional_time": ("FLOAT", {"default": 0.0, "min": 0.0, "step": 0.1}),
                "ignore_smart_quotes": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "text_input": ("STRING", {"forceInput": True}),
                "separator_symbol": ("STRING", {
                    "default": "",
                    "tooltip": "If set, text between pairs of this symbol is counted as spoken (overrides quote detection). E.g. '|' counts text between | and |.",
                }),
            },
        }

    RETURN_TYPES = ("INT", "FLOAT", "INT", "FLOAT", "INT", "FLOAT")
    RETURN_NAMES = (
        "slow_frames",
        "slow_seconds",
        "average_frames",
        "average_seconds",
        "fast_frames",
        "fast_seconds",
    )
    FUNCTION = "calculate_speech"
    CATEGORY = "APZmedia/Audio/speech"

    def calculate_speech(self, text, fps, slow_wpm, average_wpm, fast_wpm,
                         additional_time=0.0, ignore_smart_quotes=False,
                         text_input=None, separator_symbol=None):
        active_text = (
            text_input
            if (text_input is not None and isinstance(text_input, str) and text_input.strip())
            else text
        )

        sym = separator_symbol.strip() if separator_symbol and separator_symbol.strip() else None

        if sym:
            # Split on the symbol; every odd-indexed segment is spoken
            parts = active_text.split(sym)
            quoted_text = " ".join(parts[i] for i in range(1, len(parts), 2))
        else:
            # Match words inside double quotes, single quotes, and optionally smart quotes
            pattern = r'"([^"]*)"|\'([^\']*)\''
            if not ignore_smart_quotes:
                pattern += r'|\u201c([^\u201d]*)\u201d|\u2018([^\u2019]*)\u2019'
            matches = re.findall(pattern, active_text)
            quoted_text = " ".join(next((g for g in m if g), "") for m in matches)

        word_count = len(quoted_text.split()) if quoted_text.strip() else 0

        def calc(wpm):
            if word_count == 0 and additional_time == 0.0:
                return 0, 0.0
            seconds = (word_count / wpm) * 60 + additional_time
            frames = math.ceil(seconds * fps)
            return frames, round(seconds, 3)

        slow_f, slow_s = calc(slow_wpm)
        avg_f, avg_s = calc(average_wpm)
        fast_f, fast_s = calc(fast_wpm)

        return (slow_f, slow_s, avg_f, avg_s, fast_f, fast_s)
