"""Temporal smoothing filters for ARKit facial curve post-processing.

Provides two filter algorithms for reducing frame-to-frame noise in
synthesized ARKit blendshape curves:

  1. **1-Euro Filter** — Adaptive low-pass: heavy smoothing on slow movements,
     light smoothing on fast movements.  Reference: Géry Casiez et al.,
     "1€ Filter: A Simple Speed-based Low-pass Filter for Noisy Input in
     Interactive Systems", CHI 2012.

  2. **Exponential Moving Average (EMA)** — Fixed-weight low-pass with a
     single alpha parameter.

Both are pure Python (no numpy/scipy) and handle variable frame rates
via explicit time values.

Usage from arkit_remap.py:
    from temporal_smoothing import apply_temporal_smoothing, compute_smoothing_comparison
"""

import math

# ---------------------------------------------------------------------------
# Low-pass filter primitives
# ---------------------------------------------------------------------------

def _smoothing_factor(te, cutoff):
    """Compute the alpha coefficient for a given elapsed time and cutoff freq.

    alpha = 1 / (1 + tau/te)   where tau = 1 / (2*pi*cutoff)
    """
    tau = 1.0 / (2.0 * math.pi * cutoff)
    return 1.0 / (1.0 + tau / te) if te > 0 else 1.0


def _exponential_smoothing(alpha, current, previous):
    return alpha * current + (1.0 - alpha) * previous


# ---------------------------------------------------------------------------
# 1-Euro Filter
# ---------------------------------------------------------------------------

class OneEuroFilter:
    """Casiez et al. 1-Euro adaptive low-pass filter.

    Parameters:
        min_cutoff: Minimum cutoff frequency (Hz). Lower = more smoothing
                    on slow/stationary signals. Typical: 0.5–3.0 for facial.
        beta:       Speed coefficient. Higher = less lag on fast movements.
                    0 disables speed adaptation. Typical: 0.0–1.0 for facial.
        d_cutoff:   Cutoff for the derivative low-pass (Hz). Usually left
                    at 1.0; raise if derivative itself is noisy.
    """

    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None

    def reset(self):
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None

    def __call__(self, t, x):
        if self._t_prev is None:
            self._x_prev = x
            self._dx_prev = 0.0
            self._t_prev = t
            return x

        te = t - self._t_prev
        if te <= 0:
            return self._x_prev

        # Derivative estimate (low-pass filtered)
        a_d = _smoothing_factor(te, self.d_cutoff)
        dx = (x - self._x_prev) / te
        dx_hat = _exponential_smoothing(a_d, dx, self._dx_prev)

        # Adaptive cutoff based on derivative magnitude
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)

        # Signal estimate
        a = _smoothing_factor(te, cutoff)
        x_hat = _exponential_smoothing(a, x, self._x_prev)

        self._x_prev = x_hat
        self._dx_prev = dx_hat
        self._t_prev = t
        return x_hat


# ---------------------------------------------------------------------------
# Exponential Moving Average
# ---------------------------------------------------------------------------

class EMAFilter:
    """Fixed-weight exponential moving average.

    Parameters:
        alpha: Smoothing weight in (0, 1].
               1.0 = no smoothing (passthrough).
               Closer to 0 = heavier smoothing.
    """

    def __init__(self, alpha=0.5):
        self.alpha = max(0.001, min(1.0, alpha))
        self._prev = None

    def reset(self):
        self._prev = None

    def __call__(self, _t, x):
        if self._prev is None:
            self._prev = x
            return x
        self._prev = _exponential_smoothing(self.alpha, x, self._prev)
        return self._prev


# ---------------------------------------------------------------------------
# Filter factory
# ---------------------------------------------------------------------------

_FILTER_CONSTRUCTORS = {
    "one_euro": lambda params: OneEuroFilter(
        min_cutoff=params.get("minCutoff", 1.5),
        beta=params.get("beta", 0.5),
        d_cutoff=params.get("dCutoff", 1.0),
    ),
    "ema": lambda params: EMAFilter(
        alpha=params.get("alpha", 0.6),
    ),
}


def _make_filter(method, params):
    ctor = _FILTER_CONSTRUCTORS.get(method)
    if ctor is None:
        raise ValueError(
            f"Unknown smoothing method '{method}'. "
            f"Available: {list(_FILTER_CONSTRUCTORS.keys())}"
        )
    return ctor(params)


# ---------------------------------------------------------------------------
# Public API: apply smoothing pass
# ---------------------------------------------------------------------------

def apply_temporal_smoothing(arkit_output, times, smoothing_config):
    """Apply optional temporal smoothing to synthesized ARKit curves.

    This is a pure post-processing step: it does not change synthesis math,
    only filters the output time series per curve.

    Args:
        arkit_output: dict of arkit_name -> list[float] values per frame.
        times:        list[float] of frame times (seconds). Must be same
                      length as each value list. Handles variable dt.
        smoothing_config: dict from payload calibration. Expected shape::

            {
              "enabled": true,
              "method": "one_euro",
              "defaults": { "minCutoff": 1.5, "beta": 0.5, "dCutoff": 1.0 },
              "perCurveOverrides": {
                "MouthClose": { "minCutoff": 0.8, "beta": 0.3 },
                ...
              }
            }

    Returns:
        dict of arkit_name -> list[float] smoothed values. Only curves
        present in arkit_output are returned; the dict is a new object.
    """
    if not smoothing_config or not smoothing_config.get("enabled", False):
        return arkit_output

    method = smoothing_config.get("method", "one_euro")
    defaults = smoothing_config.get("defaults", {})
    overrides = smoothing_config.get("perCurveOverrides", {})

    result = {}
    for curve_name, values in arkit_output.items():
        params = dict(defaults)
        curve_override = overrides.get(curve_name, {})
        params.update(curve_override)

        filt = _make_filter(method, params)
        smoothed = []
        for i, t in enumerate(times):
            smoothed.append(filt(t, values[i]))
        result[curve_name] = smoothed

    return result


# ---------------------------------------------------------------------------
# Public API: before/after comparison
# ---------------------------------------------------------------------------

def compute_smoothing_comparison(original, smoothed, threshold=0.005):
    """Compute per-curve metrics showing how much smoothing changed signals.

    Args:
        original:  dict of arkit_name -> list[float] (pre-smoothing)
        smoothed:  dict of arkit_name -> list[float] (post-smoothing)
        threshold: Minimum absolute delta to count a frame as "altered".

    Returns:
        dict of arkit_name -> {
            "maxDelta":      float,  # largest absolute per-frame change
            "meanDelta":     float,  # average absolute per-frame change
            "alteredPct":    float,  # % of frames with |delta| > threshold
            "alteredFrames": int,    # count of frames above threshold
            "totalFrames":   int,
        }
    """
    report = {}
    for name in original:
        if name not in smoothed:
            continue
        orig_vals = original[name]
        smth_vals = smoothed[name]
        n = len(orig_vals)
        if n == 0:
            report[name] = {
                "maxDelta": 0.0, "meanDelta": 0.0,
                "alteredPct": 0.0, "alteredFrames": 0, "totalFrames": 0,
            }
            continue

        max_d = 0.0
        sum_d = 0.0
        altered = 0
        for i in range(n):
            d = abs(orig_vals[i] - smth_vals[i])
            if d > max_d:
                max_d = d
            sum_d += d
            if d > threshold:
                altered += 1

        report[name] = {
            "maxDelta": max_d,
            "meanDelta": sum_d / n,
            "alteredPct": 100.0 * altered / n,
            "alteredFrames": altered,
            "totalFrames": n,
        }

    return report
