import json

import numpy as np
import torch
from PIL import Image, ImageDraw


class AudioRegionSelector:
    """Visualise the inpaint region on a waveform and expose ms / frame controls.

    The companion JS widget (audio_region_selector.js) adds an interactive
    canvas with draggable handles and clickable word buttons.  The Python backend
    renders a static preview IMAGE showing the waveform with the selected region
    highlighted and word-boundary tick marks.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "region_start_ms": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "step": 1.0,
                    "tooltip": "Region start in milliseconds",
                }),
                "region_end_ms": ("FLOAT", {
                    "default": 500.0, "min": 0.0, "step": 1.0,
                    "tooltip": "Region end in milliseconds",
                }),
            },
            "optional": {
                "word_times_json": ("STRING", {
                    "default": "[]",
                    "tooltip": "Word timestamps JSON — shown as tick marks and word buttons in the widget",
                }),
                "fps": ("INT", {
                    "default": 24, "min": 1, "max": 240, "step": 1,
                    "tooltip": "Frames-per-second used to convert between frames and milliseconds",
                }),
                "region_start_frame": ("INT", {
                    "default": 0, "min": 0, "step": 1,
                    "tooltip": "Region start in frames (synced with region_start_ms via fps)",
                }),
                "region_end_frame": ("INT", {
                    "default": 12, "min": 0, "step": 1,
                    "tooltip": "Region end in frames (synced with region_end_ms via fps)",
                }),
                "width": ("INT", {"default": 800, "min": 256, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 160, "min": 64, "max": 1024, "step": 8}),
            },
        }

    RETURN_TYPES = ("FLOAT", "FLOAT", "IMAGE")
    RETURN_NAMES = ("region_start_ms", "region_end_ms", "waveform_preview")
    FUNCTION = "select_region"
    CATEGORY = "APZmedia/Audio/PlayDiffusion"

    # ------------------------------------------------------------------ #

    def select_region(self, audio, region_start_ms, region_end_ms,
                      word_times_json="[]", fps=24,
                      region_start_frame=0, region_end_frame=12,
                      width=800, height=160):

        waveform = audio["waveform"]
        sample_rate = audio["sample_rate"]

        if waveform.dim() == 3:
            waveform = waveform[0]
        wav = waveform.mean(dim=0) if waveform.shape[0] > 1 else waveform[0]
        samples = wav.cpu().numpy()

        total_samples = len(samples)
        total_duration_ms = (total_samples / sample_rate) * 1000.0

        # Clamp region to actual audio length
        region_start_ms = float(np.clip(region_start_ms, 0.0, total_duration_ms))
        region_end_ms = float(np.clip(region_end_ms, region_start_ms, total_duration_ms))

        try:
            word_times = json.loads(word_times_json) if word_times_json.strip() else []
        except Exception:
            word_times = []

        # ---- render ------------------------------------------------------ #
        BG      = (26, 26, 26)
        WAVE    = (78, 204, 163)
        REGION  = (255, 107, 107, 70)
        BORDER  = (255, 107, 107)
        TICK    = (255, 200, 100)
        TEXT    = (200, 200, 200)
        TEXT_DIM = (120, 120, 120)

        img = Image.new("RGB", (width, height), BG)
        draw = ImageDraw.Draw(img, "RGBA")

        # Waveform bars (one pixel per column)
        chunk = max(1, total_samples // width)
        amplitudes = np.array([
            np.max(np.abs(samples[i * chunk: min((i + 1) * chunk, total_samples)]))
            for i in range(width)
        ], dtype=np.float32)
        max_amp = amplitudes.max()
        if max_amp > 0:
            amplitudes /= max_amp

        cy = height / 2.0
        for i, amp in enumerate(amplitudes):
            bar_h = max(1.0, amp * cy * 0.9)
            draw.line([(i, int(cy - bar_h)), (i, int(cy + bar_h))], fill=WAVE)

        # Region overlay
        def ms_to_x(ms):
            if total_duration_ms <= 0:
                return 0
            return int(np.clip((ms / total_duration_ms) * width, 0, width - 1))

        x0 = ms_to_x(region_start_ms)
        x1 = ms_to_x(region_end_ms)
        if x1 > x0:
            draw.rectangle([x0, 0, x1, height], fill=REGION)
        draw.line([(x0, 0), (x0, height)], fill=BORDER, width=2)
        draw.line([(x1, 0), (x1, height)], fill=BORDER, width=2)

        # Word tick marks at top and bottom
        TICK_H = 10
        for wt in word_times:
            wx = ms_to_x(wt.get("start", 0) * 1000)
            draw.line([(wx, 0), (wx, TICK_H)], fill=TICK, width=1)
            ex = ms_to_x(wt.get("end", 0) * 1000)
            draw.line([(ex, 0), (ex, TICK_H)], fill=(*TICK, 120), width=1)

        # Time labels
        try:
            draw.text((x0 + 3, 2), f"{region_start_ms:.0f}ms", fill=TEXT)
            draw.text((max(x1 - 50, x0 + 3), height - 14),
                      f"{region_end_ms:.0f}ms", fill=TEXT)
            mid = width // 2
            draw.text((mid - 40, height - 14),
                      f"Total: {total_duration_ms:.0f}ms", fill=TEXT_DIM)
        except Exception:
            pass  # PIL text may fail if font not found; silently skip

        img_array = np.array(img).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(img_array).unsqueeze(0)

        return (region_start_ms, region_end_ms, image_tensor)
