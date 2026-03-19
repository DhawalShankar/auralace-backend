import numpy as np


def _fft_eq(y: np.ndarray, sr: int, gain_db: float, cutoff: float, boost_below: bool) -> np.ndarray:
    """
    Generic FFT-based EQ.
    boost_below=True  → bass boost  (amplify freqs BELOW cutoff)
    boost_below=False → treble boost (amplify freqs ABOVE cutoff)
    """
    Y = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(len(y), d=1.0 / sr)

    gain_linear = 10 ** (gain_db / 20.0)
    slope = 200.0  # Hz — transition width

    if boost_below:
        # Sigmoid curve: full gain below cutoff, tapering off above
        boost = 1.0 + (gain_linear - 1.0) / (1.0 + np.exp((freqs - cutoff) / slope))
    else:
        # Sigmoid curve: full gain above cutoff, tapering off below
        boost = 1.0 + (gain_linear - 1.0) / (1.0 + np.exp(-(freqs - cutoff) / slope))

    Y_boosted = Y * boost
    y_out = np.fft.irfft(Y_boosted, n=len(y))
    return y_out.astype(np.float32)


def apply_bass_boost(y: np.ndarray, sr: int, gain_db: float) -> np.ndarray:
    """
    Boost low frequencies below 250Hz.
    gain_db: 0 to 20 dB
    """
    return _fft_eq(y, sr, gain_db, cutoff=250.0, boost_below=True)


def apply_treble_boost(y: np.ndarray, sr: int, gain_db: float) -> np.ndarray:
    """
    Boost high frequencies above 4000Hz.
    gain_db: 0 to 20 dB
    """
    return _fft_eq(y, sr, gain_db, cutoff=4000.0, boost_below=False)