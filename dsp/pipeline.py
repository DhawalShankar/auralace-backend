import gc
import numpy as np
import soundfile as sf
from dsp.pitch     import apply_pitch_shift
from dsp.speed     import apply_time_stretch
from dsp.equalizer import apply_bass_boost, apply_treble_boost
from dsp.reverb    import apply_reverb
from dsp.loudness  import apply_loudness


def process_audio(
    y: np.ndarray,
    sr: int,
    pitch:    float,
    speed:    float,
    bass:     float,
    treble:   float,
    reverb:   float,
    loudness: float,
    output_path: str,
) -> np.ndarray:
    """
    Master DSP pipeline. Order matters:
    1. Speed   — time-scale modification first
    2. Pitch   — phase vocoder after speed
    3. Bass    — FFT EQ
    4. Treble  — FFT EQ
    5. Reverb  — spatial effect after EQ
    6. Loudness — final gain stage
    7. Normalize — prevent clipping

    Memory strategy: after each stage, the old array is explicitly
    dereferenced and gc.collect() is called so Python frees it before
    the next (potentially larger) stage allocates.
    """

    # 1. Speed / Time stretch
    if abs(speed - 1.0) > 0.01:
        y_new = apply_time_stretch(y, speed)
        del y
        gc.collect()
        y = y_new

    # 2. Pitch shift
    if abs(pitch) > 0.01:
        y_new = apply_pitch_shift(y, sr, pitch)
        del y
        gc.collect()
        y = y_new

    # 3. Bass boost
    if bass > 0.01:
        y_new = apply_bass_boost(y, sr, bass)
        del y
        gc.collect()
        y = y_new

    # 4. Treble boost
    if treble > 0.01:
        y_new = apply_treble_boost(y, sr, treble)
        del y
        gc.collect()
        y = y_new

    # 5. Reverb
    if reverb > 0.01:
        y_new = apply_reverb(y, sr, reverb)
        del y
        gc.collect()
        y = y_new

    # 6. Loudness gain
    if abs(loudness) > 0.01:
        y = apply_loudness(y, loudness)

    # 7. Peak normalize — prevent clipping, always applied
    max_val = np.max(np.abs(y))
    if max_val > 0:
        y = y / max_val * 0.95

    y = y.astype(np.float32)

    # Write to disk
    sf.write(output_path, y, sr, format="WAV")

    return y