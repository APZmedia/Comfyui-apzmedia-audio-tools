# APZmedia Audio Tools

## Overview

A set of ComfyUI nodes for audio and audio-adjacent work — things that are annoyingly absent from the default node library and that you'd otherwise solve with a calculator and a spreadsheet.

Two nodes, two problems:

1. You have a voiceover script and need to know how many frames of video to budget for it before you record anything.
2. You have an audio file and need a waveform image — the kind messaging apps use — because a flat timeline scrub is not a preview.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/pabloapz)

---

## Nodes

### APZmedia Speech Length Calculator

Takes a script, counts the spoken words, and tells you how many frames and seconds that speech will occupy at slow, average, and fast delivery speeds — before you book the studio or animate a single frame.

Only text inside quotation marks is counted as spoken. Everything outside is stage direction, action lines, or notes to yourself, and the node correctly does not care about any of it.

- Supports straight double quotes `"..."`, single quotes `'...'`, and smart/curly quotes `"..."` `'...'`
- **Custom separator override** — define any symbol (e.g. `|`) to mark spoken sections instead of using quotes. Text between pairs of that symbol is counted; everything else is ignored
- **Ignore smart quotes** toggle — if your script uses curly quotes for something other than speech, turn this off and only straight quotes will be matched
- WPM inputs for all three speeds — defaults are 100 / 130 / 160 but they're your numbers to change
- Additional time padding for pauses, breaths, or silence at the top or tail
- FPS input for frame count calculation (1–240)
- Optional `text_input` connector — pipe text from another node and it overrides the widget
- Outputs `frames` and `seconds` for each of the three speeds: slow, average, fast

**Category:** `APZmedia/Audio/speech`

---

### APZmedia Audio Waveform Image

Renders an audio file as a waveform bar image — the kind you see in messaging apps like WhatsApp and Telegram. Useful for audio previews, UI mockups, or anywhere you need a visual representation of sound that isn't a spectrogram.

- **Steps** controls the number of bars: fewer steps give a chunky, blocky look; more steps give a detailed waveform
- **Mode:** `mirror` (bars extend symmetrically from the centre) or `half` (bars extend from one edge — the baseline style)
- **Orientation:** `horizontal` (bars run left to right, standard waveform) or `vertical` (bars run top to bottom)
- Background and foreground colors as hex strings
- Bars have built-in spacing between them — no configuration needed, the gap is part of the look
- Amplitude is peak-normalised per bar so quiet audio still produces a readable waveform
- Multi-channel audio is mixed to mono before processing
- Output is a standard ComfyUI `IMAGE` tensor, compatible with any downstream image node

**Category:** `APZmedia/Audio`

---

## Installation

1. Clone this repo into your ComfyUI `custom_nodes` directory:
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/APZmedia/comfyui-apzmedia-audio-tools.git
   ```
2. Restart ComfyUI
3. Find nodes under the **APZmedia/Audio** category in the node menu

---

## Dependencies

- `Pillow` — for rendering the waveform image
- `torch` / `numpy` — already present in any ComfyUI installation
- `ComfyUI` — presumably already there

---

## License

MIT — use it, adapt it, don't blame us.

## Author

**Pablo Apiolazza** — [APZmedia](https://github.com/APZmedia)

## ☕ Support

If these nodes saved you time or a miscalculated voiceover budget, consider buying me a coffee.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/pabloapz)

Issues and feature requests: [GitHub repository](https://github.com/APZmedia/comfyui-apzmedia-audio-tools)
