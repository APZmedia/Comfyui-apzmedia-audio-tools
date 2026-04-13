#!/usr/bin/env python3
"""
PlayDiffusion Server - Isolated FastAPI service

Runs in a separate venv with PlayDiffusion installed.
Exposes HTTP endpoints for TTS, inpainting, and voice conversion.
"""

import io
import os
import sys
import argparse
from typing import Optional
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import uvicorn

# Try to import PlayDiffusion - this should work in the isolated venv
try:
    from playdiffusion import PlayDiffusion, TTSInput, InpaintInput, RVCInput
except ImportError:
    print("[PlayDiffusion Server] ERROR: PlayDiffusion not installed in this venv")
    print("[PlayDiffusion Server] Run: pip install git+https://github.com/playht/PlayDiffusion.git")
    sys.exit(1)

app = FastAPI(title="PlayDiffusion ComfyUI Bridge")

# Global model cache
_model_cache = {}


class TTSRequest(BaseModel):
    reference_audio_path: str
    output_text: str
    num_steps: int = 16
    temperature: float = 1.0
    diversity: float = 1.0
    guidance: float = 3.0
    audio_token_syllable_ratio: float = 3.5
    device: str = "cuda"


class InpaintRequest(BaseModel):
    audio_path: str
    input_text: str
    output_text: str
    word_times: list
    num_steps: int = 16
    temperature: float = 1.0
    diversity: float = 1.0
    guidance: float = 3.0
    audio_token_syllable_ratio: float = 3.5
    device: str = "cuda"


class RVCRequest(BaseModel):
    source_audio_path: str
    target_voice_path: str
    device: str = "cuda"


def _get_or_load_model(device: str) -> PlayDiffusion:
    """Get cached model or load new one."""
    global _model_cache
    if device not in _model_cache:
        print(f"[PlayDiffusion Server] Loading model on {device}...")
        _model_cache[device] = PlayDiffusion(device=device)
        print(f"[PlayDiffusion Server] Model loaded on {device}")
    return _model_cache[device]


@app.post("/tts")
def text_to_speech(req: TTSRequest):
    """Generate speech from text using reference voice."""
    try:
        model = _get_or_load_model(req.device)

        inp = TTSInput(
            voice=req.reference_audio_path,
            output_text=req.output_text,
            num_steps=req.num_steps,
            init_temp=req.temperature,
            init_diversity=req.diversity,
            guidance=req.guidance,
            audio_token_syllable_ratio=req.audio_token_syllable_ratio,
        )

        sample_rate, pcm = model.tts(inp)

        # Return as numpy bytes + metadata
        return {
            "sample_rate": sample_rate,
            "audio": pcm.tobytes(),
            "dtype": str(pcm.dtype),
            "shape": pcm.shape,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/inpaint")
def inpaint_audio(req: InpaintRequest):
    """Replace words in audio."""
    try:
        model = _get_or_load_model(req.device)

        inp = InpaintInput(
            audio=req.audio_path,
            input_text=req.input_text,
            output_text=req.output_text,
            input_word_times=req.word_times,
            num_steps=req.num_steps,
            init_temp=req.temperature,
            init_diversity=req.diversity,
            guidance=req.guidance,
            audio_token_syllable_ratio=req.audio_token_syllable_ratio,
        )

        sample_rate, pcm = model.inpaint(inp)

        return {
            "sample_rate": sample_rate,
            "audio": pcm.tobytes(),
            "dtype": str(pcm.dtype),
            "shape": pcm.shape,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rvc")
def voice_conversion(req: RVCRequest):
    """Convert voice style."""
    try:
        model = _get_or_load_model(req.device)

        inp = RVCInput(
            source_speech=req.source_audio_path,
            target_voice=req.target_voice_path,
        )

        sample_rate, pcm = model.rvc(inp)

        return {
            "sample_rate": sample_rate,
            "audio": pcm.tobytes(),
            "dtype": str(pcm.dtype),
            "shape": pcm.shape,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """Check server status."""
    return {"status": "ok", "loaded_devices": list(_model_cache.keys())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--models-dir", default=None, help="Path to model cache directory")
    args = parser.parse_args()

    # Set HF cache if provided
    if args.models_dir:
        os.environ["HF_HUB_CACHE"] = args.models_dir
        print(f"[PlayDiffusion Server] Using model cache: {args.models_dir}")

    print(f"[PlayDiffusion Server] Starting on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
