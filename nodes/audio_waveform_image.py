import numpy as np
import torch
from PIL import Image, ImageDraw


class AudioWaveformImage:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "width": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 128, "min": 64, "max": 4096, "step": 8}),
                "steps": ("INT", {
                    "default": 80, "min": 5, "max": 2000, "step": 1,
                    "tooltip": "Number of bars. Fewer = blockier, more = detailed.",
                }),
                "background_color": ("STRING", {"default": "#1a1a1a"}),
                "foreground_color": ("STRING", {"default": "#4ecca3"}),
                "mode": (["mirror", "half"],),
                "orientation": (["horizontal", "vertical"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("waveform_image",)
    FUNCTION = "generate_waveform"
    CATEGORY = "APZmedia/Audio"

    def _parse_color(self, color_str):
        h = color_str.strip().lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def generate_waveform(self, audio, width, height, steps, background_color,
                          foreground_color, mode, orientation):
        # Mix to mono
        wav = audio["waveform"][0]  # (channels, samples)
        wav = wav.mean(dim=0) if wav.shape[0] > 1 else wav[0]
        samples = wav.cpu().numpy()

        # Compute peak amplitude per bar
        chunk = max(1, len(samples) // steps)
        amplitudes = np.array([
            np.max(np.abs(samples[i * chunk: min((i + 1) * chunk, len(samples))]))
            for i in range(steps)
        ])
        max_amp = amplitudes.max()
        if max_amp > 0:
            amplitudes /= max_amp

        bg = self._parse_color(background_color)
        fg = self._parse_color(foreground_color)

        img = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(img)

        GAP = 0.2  # 20% of each slot is gap between bars

        if orientation == "horizontal":
            slot_w = width / steps
            bar_w = max(1.0, slot_w * (1.0 - GAP))
            cy = height / 2.0
            for i, amp in enumerate(amplitudes):
                xc = (i + 0.5) * slot_w
                x0, x1 = int(xc - bar_w / 2), int(xc + bar_w / 2)
                if mode == "mirror":
                    bh = amp * cy
                    draw.rectangle([x0, int(cy - bh), x1, int(cy + bh)], fill=fg)
                else:
                    bh = amp * height * 0.92
                    draw.rectangle([x0, int(height - bh), x1, height], fill=fg)
        else:  # vertical
            slot_h = height / steps
            bar_h = max(1.0, slot_h * (1.0 - GAP))
            cx = width / 2.0
            for i, amp in enumerate(amplitudes):
                yc = (i + 0.5) * slot_h
                y0, y1 = int(yc - bar_h / 2), int(yc + bar_h / 2)
                if mode == "mirror":
                    bw = amp * cx
                    draw.rectangle([int(cx - bw), y0, int(cx + bw), y1], fill=fg)
                else:
                    bw = amp * width * 0.92
                    draw.rectangle([0, y0, int(bw), y1], fill=fg)

        img_array = np.array(img).astype(np.float32) / 255.0
        return (torch.from_numpy(img_array).unsqueeze(0),)
