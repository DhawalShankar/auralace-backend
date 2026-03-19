from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from dsp.pipeline import process_audio
from utils.file_handler import save_upload, cleanup_input
from utils.waveform import get_waveform_data
import os
import uuid
import gc
import librosa
import numpy as np

router = APIRouter()

# Hard limits to protect the 512MB Render free tier
MAX_FILE_BYTES    = 15 * 1024 * 1024   # 15 MB upload limit
MAX_DURATION_SECS = 300                 # 5 minutes max audio length

@router.post("/process/")
async def process_audio_route(
    audio: UploadFile = File(...),
    pitch:    float = Form(0.0),
    speed:    float = Form(1.0),
    bass:     float = Form(0.0),
    treble:   float = Form(0.0),
    reverb:   float = Form(0.0),
    loudness: float = Form(0.0),
):
    # ── Validate file type ──────────────────────────────────────────────────
    allowed = ["audio/wav", "audio/wave", "audio/mpeg", "audio/mp3", "audio/x-wav"]
    filename = audio.filename or ""
    if audio.content_type not in allowed and not filename.endswith((".wav", ".mp3")):
        raise HTTPException(status_code=400, detail="Only WAV and MP3 files are supported.")

    # ── Validate file size before reading ──────────────────────────────────
    # Read in chunks to check size without loading entire file into RAM first
    chunks = []
    total = 0
    while True:
        chunk = await audio.read(64 * 1024)  # 64KB chunks
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum allowed size is {MAX_FILE_BYTES // (1024*1024)}MB."
            )
        chunks.append(chunk)
    file_bytes = b"".join(chunks)
    del chunks  # free chunk list immediately
    gc.collect()

    # ── Clamp parameters ───────────────────────────────────────────────────
    pitch    = max(-12.0, min(12.0,  pitch))
    speed    = max(0.5,   min(2.0,   speed))
    bass     = max(0.0,   min(20.0,  bass))
    treble   = max(0.0,   min(20.0,  treble))
    reverb   = max(0.0,   min(100.0, reverb))
    loudness = max(-20.0, min(20.0,  loudness))

    # ── Save uploaded file ─────────────────────────────────────────────────
    uid = str(uuid.uuid4())[:8]
    ext = os.path.splitext(filename)[1] or ".wav"
    input_path  = f"media/input_{uid}{ext}"
    output_path = f"media/output_{uid}.wav"

    os.makedirs("media", exist_ok=True)
    with open(input_path, "wb") as f:
        f.write(file_bytes)
    del file_bytes  # free raw bytes — no longer needed
    gc.collect()

    try:
        # ── Load audio (mono only — halves RAM for stereo files) ───────────
        y, sr = librosa.load(input_path, sr=None, mono=True)

        # ── Validate duration ──────────────────────────────────────────────
        duration = len(y) / sr
        if duration > MAX_DURATION_SECS:
            raise HTTPException(
                status_code=400,
                detail=f"Audio too long. Maximum allowed duration is {MAX_DURATION_SECS // 60} minutes."
            )

        # ── Capture original waveform data BEFORE processing ──────────────
        # Store only the 200-point summary — not the full array
        original_waveform  = get_waveform_data(y)
        duration_original  = round(duration, 2)

        # ── Run DSP pipeline ───────────────────────────────────────────────
        # Pass y directly — no .copy(). Pipeline overwrites y stage by stage.
        # Original waveform is already captured above so we don't need it anymore.
        y_processed = process_audio(
            y=y,           # no .copy() — saves one full array worth of RAM
            sr=sr,
            pitch=pitch,
            speed=speed,
            bass=bass,
            treble=treble,
            reverb=reverb,
            loudness=loudness,
            output_path=output_path,
        )

        # ── Free original array — we only need processed from here ────────
        del y
        gc.collect()

        # ── Build response ─────────────────────────────────────────────────
        processed_waveform = get_waveform_data(y_processed)
        duration_processed = round(len(y_processed) / sr, 2)

        del y_processed  # free processed array — it's written to disk already
        gc.collect()

        return JSONResponse({
            "url":                f"/media/output_{uid}.wav",
            "filename":           f"output_{uid}.wav",
            "original_waveform":  original_waveform,
            "processed_waveform": processed_waveform,
            "duration_original":  duration_original,
            "duration_processed": duration_processed,
            "sample_rate":        sr,
        })

    except HTTPException:
        raise  # re-raise our own validation errors as-is

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    finally:
        cleanup_input(input_path)
        gc.collect()  # always sweep on exit