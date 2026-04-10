# APZmedia Audio Tools

## Overview

A set of ComfyUI nodes for audio and audio-adjacent work — things that are annoyingly absent from the default node library and that you'd otherwise solve with a calculator and a spreadsheet.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/pabloapz)

---

## Installation

### Via ComfyUI Manager (recommended)

Search for **APZmedia Audio Tools** in ComfyUI Manager and click Install. Dependencies are installed automatically.

### Manual

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/APZmedia/comfyui-apzmedia-audio-tools.git
cd comfyui-apzmedia-audio-tools
pip install -r requirements.txt
```

Restart ComfyUI. Nodes appear under the **APZmedia/Audio** and **APZmedia/Audio/PlayDiffusion** categories.

---

## Nodes

### PlayDiffusion — Speech Inpainting

> Requires ~10 GB of model weights downloaded on first use (stored in `ComfyUI/models/playdiffusion/`).

A set of nodes wrapping [PlayHT/PlayDiffusion](https://github.com/playht/PlayDiffusion) — a non-autoregressive diffusion model that edits specific words in existing speech without regenerating the whole clip. Surrounding audio remains untouched and the speaker's voice is preserved.

#### PlayDiffusion Loader

Loads the PlayDiffusion model onto GPU or CPU. Weights are downloaded from HuggingFace automatically on first run and cached in `ComfyUI/models/playdiffusion/`. Subsequent runs load from cache instantly.

**Category:** `APZmedia/Audio/PlayDiffusion`

---

#### PlayDiffusion Inpaint

Replaces one or more words in existing speech audio. Provide the original and edited transcript; the model reconstructs only the changed region, blending seamlessly with the surrounding audio.

- **audio** — source speech clip
- **input_text** — the full original transcript
- **output_text** — the transcript with your edits (change only the word(s) you want to replace)
- **word_times_json** — word-level timestamps from the Audio Transcribe node
- **num_steps** — diffusion denoising steps (default 16; more = higher quality but slower)
- **temperature / diversity / guidance** — sampling controls

Best used downstream of **Audio Transcribe → Word Replacer**, which builds the correct inputs automatically.

**Category:** `APZmedia/Audio/PlayDiffusion`

---

#### PlayDiffusion TTS

Synthesises speech from text in the voice of a reference speaker. No voice training required — a short reference clip is enough.

- **reference_audio** — clip of the target voice (a few seconds is sufficient)
- **output_text** — text to synthesise

**Category:** `APZmedia/Audio/PlayDiffusion`

---

#### PlayDiffusion Voice Conversion

Transfers the timbre of a target voice onto source speech without altering the words.

- **source_audio** — the speech whose content you want to keep
- **target_voice** — the voice you want it to sound like

**Category:** `APZmedia/Audio/PlayDiffusion`

---

### PlayDiffusion Utilities

#### Audio Transcribe (Whisper)

Transcribes audio with word-level timestamps using a local [faster-whisper](https://github.com/SYSTRAN/faster-whisper) model. No internet connection or API key required after the first download. Models are stored in `ComfyUI/models/whisper/`.

- **model_size** — `tiny` / `base` / `small` / `medium` / `large-v3` (trade off speed vs accuracy)
- **language** — ISO-639-1 code (e.g. `en`, `es`) or leave blank to auto-detect
- **device** — `cuda` or `cpu`

Outputs a plain **transcript** string and a **word_times_json** string:
```json
[
  { "word": "hello", "start": 0.04, "end": 0.32 },
  { "word": "world", "start": 0.36, "end": 0.72 }
]
```

**Category:** `APZmedia/Audio/PlayDiffusion`

---

#### Word Replacer

Takes a transcript and its word timestamps, replaces a phrase, and produces everything the PlayDiffusion Inpaint node needs in one step.

- **original_phrase** — the word or phrase to replace (case-insensitive, multi-word supported)
- **replacement_phrase** — what to replace it with
- Outputs **input_text**, **output_text**, **word_times_json** (passthrough), and the **region_start_ms** / **region_end_ms** of the replaced region for the Audio Region Selector

**Category:** `APZmedia/Audio/PlayDiffusion`

---

#### Audio Region Selector

Visualises the inpaint region on a waveform and provides interactive controls for fine-tuning the selection. Useful for inspecting and manually adjusting the region before running inpainting.

**Interactive JS widget (in the node UI):**
- Canvas showing a timeline with a draggable red region (drag the handles or the shaded area)
- Word buttons — click any word from the timestamp JSON to snap the region to that word's timing
- All four controls stay in sync:
  - `region_start_ms` / `region_end_ms` — position in milliseconds
  - `region_start_frame` / `region_end_frame` — position in frames (converted via the `fps` input)

**Static IMAGE output:** a waveform preview with the selected region highlighted in red and word tick marks at the top — useful for logging or visual confirmation downstream.

**Category:** `APZmedia/Audio/PlayDiffusion`

---

### Typical Inpaint Workflow

```
[Load Audio]
    │
    ▼
[Audio Transcribe]  ──►  transcript + word_times_json
                                   │
                         [Word Replacer]
                         original:    "Neo"
                         replacement: "Trinity"
                                   │
              ┌────────────────────┤
              │                    │
    input/output text     region_start_ms / region_end_ms
              │                    │
    [Audio Region Selector] ◄──────┘   (visual check + fine-tune)
              │
    [PlayDiffusion Loader] ──► model
              │
    [PlayDiffusion Inpaint]
              │
         [Save Audio]
```

---

### Audio Utility Nodes

#### Speech Length Calculator

Takes a script, counts the spoken words, and tells you how many frames and seconds that speech will occupy at slow, average, and fast delivery speeds — before you book the studio or animate a single frame.

Only text inside quotation marks is counted as spoken. Everything outside is stage direction, action lines, or notes to yourself, and the node correctly does not care about any of it.

- Supports straight double quotes `"..."`, single quotes `'...'`, and smart/curly quotes `"..."` `'...'`
- **Custom separator override** — define any symbol (e.g. `|`) to mark spoken sections instead of using quotes
- **Ignore smart quotes** toggle
- WPM inputs for all three speeds (defaults: 100 / 130 / 160)
- Additional time padding for pauses, breaths, or silence
- FPS input for frame count calculation (1–240)
- Optional `text_input` connector — pipe text from another node

**Category:** `APZmedia/Audio/speech`

---

#### Audio Waveform Image

Renders an audio file as a waveform bar image — the kind you see in messaging apps. Useful for audio previews, UI mockups, or anywhere you need a visual representation of sound.

- **Steps** — number of bars
- **Mode:** `mirror` (symmetrical) or `half` (baseline style)
- **Orientation:** `horizontal` or `vertical`
- Background and foreground colors as hex strings
- Amplitude is peak-normalised; multi-channel audio is mixed to mono

**Category:** `APZmedia/Audio`

---

#### Audio Equalizer

A parametric EQ node with a visual DaVinci Resolve-style curve editor. Up to 6 bands; each band is draggable on a frequency × gain canvas.

- Filter types: peak, low shelf, high shelf, low pass, high pass
- Double-click the canvas to add a band; right-click to cycle filter type; scroll wheel to adjust Q
- Outputs processed audio at the same sample rate as the input

**Category:** `APZmedia/Audio`

---

## Model Storage

| Model | Location | Size |
|---|---|---|
| PlayDiffusion weights | `ComfyUI/models/playdiffusion/` | ~10 GB |
| Whisper tiny | `ComfyUI/models/whisper/` | ~75 MB |
| Whisper base | `ComfyUI/models/whisper/` | ~145 MB |
| Whisper small | `ComfyUI/models/whisper/` | ~460 MB |
| Whisper medium | `ComfyUI/models/whisper/` | ~1.5 GB |
| Whisper large-v3 | `ComfyUI/models/whisper/` | ~3 GB |

All models are downloaded automatically on first use. PlayDiffusion fetches from [PlayHT/PlayDiffusion](https://huggingface.co/PlayHT/PlayDiffusion) on HuggingFace; Whisper fetches from the faster-whisper repository.

---

## Dependencies

Installed automatically via `requirements.txt`:

- [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) — local Whisper transcription
- [`playdiffusion`](https://github.com/playht/PlayDiffusion) — PlayHT's speech diffusion library

Already present in any ComfyUI environment:

- `torch` / `torchaudio` / `numpy` / `Pillow`

---

## License

MIT — use it, adapt it, don't blame us.

## Author

**Pablo Apiolazza** — [APZmedia](https://github.com/APZmedia)

## Support

If these nodes saved you time or a miscalculated voiceover budget, consider buying me a coffee.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/pabloapz)

Issues and feature requests: [GitHub repository](https://github.com/APZmedia/comfyui-apzmedia-audio-tools)
