from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from dsp.pipeline import process_audio
from utils.file_handler import cleanup_input
from utils.waveform import get_waveform_data
import os
import uuid
import gc
import base64
import librosa

router = APIRouter()

# Hard limits to protect the 512MB Render free tier
MAX_FILE_BYTES    = 15 * 1024 * 1024  # 15 MB upload limit
MAX_DURATION_SECS = 300               # 5 minutes max audio length

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
    # ── Validate file type ─────────────────────────────────────────────────
    allowed = ["audio/wav", "audio/wave", "audio/mpeg", "audio/mp3", "audio/x-wav"]
    filename = audio.filename or ""
    if audio.content_type not in allowed and not filename.endswith((".wav", ".mp3")):
        raise HTTPException(status_code=400, detail="Only WAV and MP3 files are supported.")

    # ── Read file in chunks, enforce size limit ────────────────────────────
    chunks = []
    total = 0
    while True:
        chunk = await audio.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum allowed size is {MAX_FILE_BYTES // (1024 * 1024)}MB."
            )
        chunks.append(chunk)
    file_bytes = b"".join(chunks)
    del chunks
    gc.collect()

    # ── Clamp parameters ───────────────────────────────────────────────────
    pitch    = max(-12.0, min(12.0,  pitch))
    speed    = max(0.5,   min(2.0,   speed))
    bass     = max(0.0,   min(20.0,  bass))
    treble   = max(0.0,   min(20.0,  treble))
    reverb   = max(0.0,   min(100.0, reverb))
    loudness = max(-20.0, min(20.0,  loudness))

    # ── Write input to a temp file (librosa needs a file path) ────────────
    uid        = str(uuid.uuid4())[:8]
    ext        = os.path.splitext(filename)[1] or ".wav"
    input_path = f"/tmp/input_{uid}{ext}"
    output_path = f"/tmp/output_{uid}.wav"

    os.makedirs("/tmp", exist_ok=True)
    with open(input_path, "wb") as f:
        f.write(file_bytes)
    del file_bytes
    gc.collect()

    try:
        # ── Load audio ─────────────────────────────────────────────────────
        y, sr = librosa.load(input_path, sr=None, mono=True)

        # ── Validate duration ──────────────────────────────────────────────
        duration = len(y) / sr
        if duration > MAX_DURATION_SECS:
            raise HTTPException(
                status_code=400,
                detail=f"Audio too long. Maximum allowed duration is {MAX_DURATION_SECS // 60} minutes."
            )

        # ── Capture original waveform summary before pipeline mutates y ───
        original_waveform = get_waveform_data(y)
        duration_original = round(duration, 2)

        # ── Run DSP pipeline ───────────────────────────────────────────────
        y_processed = process_audio(
            y=y,
            sr=sr,
            pitch=pitch,
            speed=speed,
            bass=bass,
            treble=treble,
            reverb=reverb,
            loudness=loudness,
            output_path=output_path,
        )

        del y
        gc.collect()

        # ── Collect response data from processed array ─────────────────────
        processed_waveform = get_waveform_data(y_processed)
        duration_processed = round(len(y_processed) / sr, 2)

        del y_processed
        gc.collect()

        # ── Read the written WAV file and encode as base64 ─────────────────
        # This way the audio travels in the JSON response itself.
        # No persistent disk needed — survives Render restarts and cold starts.
        with open(output_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")

        return JSONResponse({
            "audio_b64":          audio_b64,        # base64-encoded WAV
            "filename":           f"output_{uid}.wav",
            "original_waveform":  original_waveform,
            "processed_waveform": processed_waveform,
            "duration_original":  duration_original,
            "duration_processed": duration_processed,
            "sample_rate":        sr,
        })

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    finally:
        # Clean up both input and output temp files
        cleanup_input(input_path)
        cleanup_input(output_path)
        gc.collect()