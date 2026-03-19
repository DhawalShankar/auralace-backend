import numpy as np


def apply_loudness(y: np.ndarray, gain_db: float) -> np.ndarray:
    """
    Apply linear gain to audio signal.
    gain_db: -20 to +20 dB
    Positive = louder, Negative = quieter
    """
    gain_linear = 10 ** (gain_db / 20.0)
    return (y * gain_linear).astype(np.float32)