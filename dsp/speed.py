import numpy as np
import librosa


def apply_time_stretch(y: np.ndarray, rate: float) -> np.ndarray:
    """
    Time-stretch audio without changing pitch.
    rate > 1.0 = faster (shorter duration)
    rate < 1.0 = slower (longer duration)
    Range: 0.5x to 2.0x
    """
    return librosa.effects.time_stretch(y, rate=rate)