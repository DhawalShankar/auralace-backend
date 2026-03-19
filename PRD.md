# AuraLace Backend — PRD & Structure

## What We're Building

A FastAPI backend that receives an audio file + 6 DSP parameters, processes the audio using Python signal processing libraries, and returns the processed file URL along with waveform data for visualization.

---

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| Framework | FastAPI | Async, fast, auto docs, perfect for ML/DSP APIs |
| DSP | Librosa | Pitch shift, time stretch, audio loading |
| DSP | NumPy | FFT, array math, bass/treble EQ |
| DSP | SciPy | Convolution for reverb |
| Audio I/O | Soundfile | Save processed WAV files |
| Server | Uvicorn | ASGI server for FastAPI |
| CORS | FastAPI middleware | Allow Next.js frontend to call backend |

---

## Folder Structure

```
auralace-backend/
│
├── main.py                  # FastAPI app entry point
├── requirements.txt         # All dependencies
├── .env                     # Environment variables
│
├── api/
│   ├── __init__.py
│   └── routes.py            # POST /api/process/ endpoint
│
├── dsp/
│   ├── __init__.py
│   ├── pipeline.py          # Master DSP pipeline — calls all transforms
│   ├── pitch.py             # Pitch shift using librosa
│   ├── speed.py             # Time stretch using librosa
│   ├── equalizer.py         # Bass + Treble boost using FFT
│   ├── reverb.py            # Reverb using scipy convolution
│   └── loudness.py          # Loudness/gain control
│
├── utils/
│   ├── __init__.py
│   ├── file_handler.py      # Save/delete uploaded + output files
│   └── waveform.py          # Downsample audio → waveform data for frontend
│
└── media/                   # Temp storage for processed files
    └── .gitkeep
```

---

## API Contract

### `POST /api/process/`

**Request** — `multipart/form-data`

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `audio` | File | WAV/MP3 | Input audio file |
| `pitch` | float | -12 to +12 | Semitones to shift |
| `speed` | float | 0.5 to 2.0 | Time stretch rate |
| `bass` | float | 0 to 20 | Bass boost in dB |
| `treble` | float | 0 to 20 | Treble boost in dB |
| `reverb` | float | 0 to 100 | Reverb wet mix % |
| `loudness` | float | -20 to +20 | Output gain in dB |

**Response** — `application/json`

```json
{
  "url": "/media/output_abc123.wav",
  "filename": "output_abc123.wav",
  "original_waveform": [0.1, 0.4, 0.8, ...],
  "processed_waveform": [0.2, 0.5, 0.9, ...],
  "duration_original": 12.34,
  "duration_processed": 10.28,
  "sample_rate": 22050
}
```

---

## DSP Pipeline — How Each Transform Works

### 1. Pitch Shift
```
librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch)
```
Uses phase vocoder internally. Shifts pitch without changing duration.

### 2. Speed / Time Stretch
```
librosa.effects.time_stretch(y, rate=speed)
```
Stretches or compresses audio in time without changing pitch. Rate > 1 = faster, Rate < 1 = slower.

### 3. Bass Boost
```
FFT → amplify frequencies below 250Hz → IFFT
```
Convert to frequency domain, apply gain curve to low frequencies, convert back.

### 4. Treble Boost
```
FFT → amplify frequencies above 4000Hz → IFFT
```
Same as bass but targets high frequency bands.

### 5. Reverb
```
scipy.signal.fftconvolve(y, impulse_response)
```
Creates a synthetic room impulse response, convolves with audio. Wet/dry mix controlled by reverb % parameter.

### 6. Loudness
```
y = y * (10 ** (loudness_db / 20))
```
Simple linear gain applied after all other transforms. Followed by peak normalization to prevent clipping.

---

## Processing Order

Order matters in DSP — wrong order = bad results.

```
Load Audio
    ↓
Speed Change        ← first, affects duration
    ↓
Pitch Shift         ← after speed, uses phase vocoder
    ↓
Bass Boost (FFT)    ← frequency domain EQ
    ↓
Treble Boost (FFT)  ← frequency domain EQ
    ↓
Reverb              ← spatial effect, applied after EQ
    ↓
Loudness Gain       ← last, controls final output level
    ↓
Peak Normalize      ← prevent clipping
    ↓
Save as WAV
    ↓
Return URL + Waveform Data
```

---

## File Lifecycle

```
Upload → save as input_abc123.mp3
Process → save as output_abc123.wav
Return URL → frontend downloads/plays
Cleanup → delete input file immediately after processing
          delete output file after 10 minutes (optional)
```

---

## Error Handling

| Scenario | HTTP Code | Message |
|----------|-----------|---------|
| No file uploaded | 400 | "No audio file provided" |
| Invalid file type | 400 | "Only WAV and MP3 supported" |
| File too large | 413 | "File exceeds 50MB limit" |
| DSP processing fails | 500 | "Processing failed: {detail}" |
| Invalid parameters | 422 | FastAPI auto-validation |

---

## `requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9
librosa==0.10.2
numpy==1.26.4
scipy==1.13.0
soundfile==0.12.1
python-dotenv==1.0.1
```

---

## Local Setup Commands

```bash
# Create project
mkdir auralace-backend && cd auralace-backend
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install deps
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8000
```

---

## Render Deployment Plan

```
Service Type  : Web Service
Runtime       : Python 3.11
Build Command : pip install -r requirements.txt
Start Command : uvicorn main:app --host 0.0.0.0 --port $PORT
```

For MP3 support on Render, add this to build command:
```
apt-get install -y ffmpeg && pip install -r requirements.txt
```

---

Ready to start coding? Shall I write all files one by one starting with `main.py`? 🚀