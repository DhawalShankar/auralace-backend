from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from dsp.pipeline import process_audio
from utils.file_handler import save_upload, cleanup_input
from utils.waveform import get_waveform_data
import os
import uuid
import librosa

router = APIRouter()


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
    # Validate file type
    allowed = ["audio/wav", "audio/wave", "audio/mpeg", "audio/mp3", "audio/x-wav"]
    filename = audio.filename or ""
    if audio.content_type not in allowed and not filename.endswith((".wav", ".mp3")):
        raise HTTPException(status_code=400, detail="Only WAV and MP3 files are supported")

    # Clamp parameters to safe ranges
    pitch    = max(-12.0, min(12.0,  pitch))
    speed    = max(0.5,   min(2.0,   speed))
    bass     = max(0.0,   min(20.0,  bass))
    treble   = max(0.0,   min(20.0,  treble))
    reverb   = max(0.0,   min(100.0, reverb))
    loudness = max(-20.0, min(20.0,  loudness))

    # Save uploaded file
    uid = str(uuid.uuid4())[:8]
    ext = os.path.splitext(filename)[1] or ".wav"
    input_path  = f"media/input_{uid}{ext}"
    output_path = f"media/output_{uid}.wav"

    await save_upload(audio, input_path)

    try:
        # Load original audio for waveform
        y_original, sr = librosa.load(input_path, sr=None, mono=True)

        # Run DSP pipeline
        y_processed = process_audio(
            y=y_original.copy(),
            sr=sr,
            pitch=pitch,
            speed=speed,
            bass=bass,
            treble=treble,
            reverb=reverb,
            loudness=loudness,
            output_path=output_path,
        )

        return JSONResponse({
            "url":                f"/media/output_{uid}.wav",
            "filename":           f"output_{uid}.wav",
            "original_waveform":  get_waveform_data(y_original),
            "processed_waveform": get_waveform_data(y_processed),
            "duration_original":  round(len(y_original) / sr, 2),
            "duration_processed": round(len(y_processed) / sr, 2),
            "sample_rate":        sr,
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    finally:
        cleanup_input(input_path)