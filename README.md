# 🎧 AuraLace — Backend API

> Premium Audio Digital Signal Processing Engine  
> Built with FastAPI · Librosa · NumPy · SciPy
---

## Overview

AuraLace Backend is a high-performance DSP (Digital Signal Processing) API that powers real-time audio transformation. It accepts audio files and applies up to 6 signal processing transforms, returning processed audio along with waveform data for visualization.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| DSP Engine | Librosa |
| Math & FFT | NumPy |
| Convolution | SciPy |
| Audio I/O | SoundFile |
| Server | Uvicorn |

---

## Features

- **Pitch Shift** — Shift pitch up or down by semitones using phase vocoder
- **Time Stretch** — Speed up or slow down audio without affecting pitch
- **Bass Boost** — Amplify low frequencies via FFT-based EQ (below 250Hz)
- **Treble Boost** — Amplify high frequencies via FFT-based EQ (above 4000Hz)
- **Reverb** — Apply room/hall effect using convolution with synthetic impulse response
- **Loudness** — Control output gain in dB
- **Waveform Data** — Returns downsampled waveform arrays for frontend visualization

---

## Project Structure

```
auralace-backend/
│
├── main.py                  # FastAPI app entry point
├── requirements.txt         # Dependencies
├── .env                     # Environment variables
│
├── api/
│   ├── __init__.py
│   └── routes.py            # POST /api/process/ endpoint
│
├── dsp/
│   ├── __init__.py
│   ├── pipeline.py          # Master DSP pipeline
│   ├── pitch.py             # Pitch shift
│   ├── speed.py             # Time stretch
│   ├── equalizer.py         # Bass + Treble FFT EQ
│   ├── reverb.py            # Convolution reverb
│   └── loudness.py          # Output gain
│
├── utils/
│   ├── __init__.py
│   ├── file_handler.py      # Upload/cleanup handlers
│   └── waveform.py          # Waveform downsampling
│
└── media/                   # Temporary audio file storage
```

---

## API Reference

### `POST /api/process/`

Processes an audio file with the given DSP parameters.

**Request** — `multipart/form-data`

| Field | Type | Range | Default | Description |
|-------|------|-------|---------|-------------|
| `audio` | File | WAV / MP3 | required | Input audio file |
| `pitch` | float | -12 to +12 | 0 | Semitones to shift |
| `speed` | float | 0.5 to 2.0 | 1.0 | Time stretch rate |
| `bass` | float | 0 to 20 | 0 | Bass boost in dB |
| `treble` | float | 0 to 20 | 0 | Treble boost in dB |
| `reverb` | float | 0 to 100 | 0 | Reverb wet mix % |
| `loudness` | float | -20 to +20 | 0 | Output gain in dB |

**Response** — `application/json`

```json
{
  "url": "/media/output_abc123.wav",
  "filename": "output_abc123.wav",
  "original_waveform": [0.12, 0.45, 0.78, "..."],
  "processed_waveform": [0.18, 0.52, 0.81, "..."],
  "duration_original": 12.34,
  "duration_processed": 10.28,
  "sample_rate": 22050
}
```

**Error Responses**

| Code | Reason |
|------|--------|
| 400 | Invalid file type |
| 422 | Invalid parameters |
| 500 | DSP processing failed |

---

## DSP Pipeline Order

Order of transforms matters significantly in signal processing:

```
Audio Input
    │
    ▼
1. Time Stretch      ← change duration first
    │
    ▼
2. Pitch Shift       ← phase vocoder after speed change
    │
    ▼
3. Bass Boost        ← FFT EQ (low frequencies)
    │
    ▼
4. Treble Boost      ← FFT EQ (high frequencies)
    │
    ▼
5. Reverb            ← spatial effect after EQ
    │
    ▼
6. Loudness Gain     ← final output level control
    │
    ▼
7. Peak Normalize    ← prevent clipping (auto)
    │
    ▼
Audio Output (WAV)
```

---

## Local Setup

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/auralace-backend.git
cd auralace-backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Development Server

```bash
python -m uvicorn main:app --reload --port 8000
```

### API Documentation

Once running, visit:
- Swagger UI → `http://localhost:8000/docs`
- ReDoc → `http://localhost:8000/redoc`
- Health Check → `http://localhost:8000`

---

## Deployment — Render

| Setting | Value |
|---------|-------|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |

For MP3 support on Render, use this build command:
```
apt-get install -y ffmpeg && pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the root directory:

```env
MEDIA_DIR=media
MAX_FILE_SIZE_MB=50
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## Frontend

This backend is designed to work with the **AuraLace Frontend** built with Next.js.

Once deployed, update your frontend `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://your-render-url.onrender.com
```

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

MIT License — open source and free to use.

---

<div align="center">
  <strong>Built with ❤️ using FastAPI · Librosa · NumPy · SciPy</strong>
</div>