import numpy as np
import librosa


def apply_pitch_shift(y: np.ndarray, sr: int, semitones: float) -> np.ndarray:
    """
    Shift pitch by N semitones using librosa phase vocoder.
    Positive = higher pitch, Negative = lower pitch.
    Range: -12 to +12 semitones (one octave each way)
    """
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)