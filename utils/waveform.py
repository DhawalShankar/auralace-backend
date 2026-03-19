import numpy as np
from typing import List


def get_waveform_data(y: np.ndarray, num_points: int = 200) -> List[float]:
    """
    Downsample audio array to num_points for frontend waveform visualization.
    Returns list of peak amplitudes per chunk.
    """
    if len(y) == 0:
        return [0.0] * num_points

    chunk_size = max(1, len(y) // num_points)
    waveform = []

    for i in range(0, len(y), chunk_size):
        chunk = y[i:i + chunk_size]
        peak = float(np.max(np.abs(chunk)))
        waveform.append(round(peak, 4))

    # Trim or pad to exactly num_points
    waveform = waveform[:num_points]
    while len(waveform) < num_points:
        waveform.append(0.0)

    return waveform