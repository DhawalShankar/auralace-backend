import numpy as np
from scipy.signal import fftconvolve


def _generate_impulse_response(sr: int, decay: float = 1.5, room_size: float = 0.5) -> np.ndarray:
    """
    Generate a synthetic room impulse response (IR).
    decay     : reverb tail length in seconds
    room_size : 0.0 (small room) to 1.0 (large hall)
    """
    length = int(sr * decay)
    # Exponential decay envelope
    t = np.linspace(0, decay, length)
    envelope = np.exp(-t * (3.0 / (room_size + 0.1)))
    # White noise as the IR
    noise = np.random.randn(length)
    ir = noise * envelope
    # Normalize IR
    ir = ir / (np.max(np.abs(ir)) + 1e-8)
    return ir.astype(np.float32)


def apply_reverb(y: np.ndarray, sr: int, wet_percent: float) -> np.ndarray:
    """
    Apply convolution reverb using a synthetic room IR.
    wet_percent: 0 (dry) to 100 (fully wet)
    """
    wet = wet_percent / 100.0
    dry = 1.0 - (wet * 0.5)  # keep some dry signal always

    # Scale room size with wet amount
    room_size = wet * 0.8
    ir = _generate_impulse_response(sr, decay=1.2 + wet, room_size=room_size)

    # Convolve
    y_wet = fftconvolve(y, ir, mode="full")[:len(y)]
    y_wet = y_wet.astype(np.float32)

    # Normalize wet signal to match dry level
    dry_rms = np.sqrt(np.mean(y ** 2)) + 1e-8
    wet_rms = np.sqrt(np.mean(y_wet ** 2)) + 1e-8
    y_wet = y_wet * (dry_rms / wet_rms)

    # Mix dry + wet
    y_out = dry * y + wet * y_wet
    return y_out.astype(np.float32)