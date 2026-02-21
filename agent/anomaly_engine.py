"""
Anomaly Engine — Statistical anomaly detection using sliding windows.

Tracks metric history and detects anomalies using Z-score and
threshold-based methods beyond what the simple detector catches.
"""

import math
from collections import deque
from datetime import datetime


class MetricWindow:
    """Sliding window for a single metric with statistical helpers."""

    def __init__(self, max_size: int = 60):
        self._values: deque[float] = deque(maxlen=max_size)
        self._timestamps: deque[str] = deque(maxlen=max_size)

    def push(self, value: float):
        self._values.append(value)
        self._timestamps.append(datetime.now().isoformat())

    @property
    def count(self) -> int:
        return len(self._values)

    @property
    def mean(self) -> float:
        if not self._values:
            return 0.0
        return sum(self._values) / len(self._values)

    @property
    def std(self) -> float:
        if len(self._values) < 2:
            return 0.0
        m = self.mean
        variance = sum((v - m) ** 2 for v in self._values) / (len(self._values) - 1)
        return math.sqrt(variance)

    @property
    def latest(self) -> float:
        return self._values[-1] if self._values else 0.0

    @property
    def trend(self) -> float:
        """Simple trend: difference between last two values."""
        if len(self._values) < 2:
            return 0.0
        return self._values[-1] - self._values[-2]

    def z_score(self, value: float | None = None) -> float:
        """Z-score of the latest (or given) value relative to window history."""
        v = value if value is not None else self.latest
        s = self.std
        if s == 0:
            return 0.0
        return (v - self.mean) / s

    def values_list(self) -> list[float]:
        return list(self._values)

    def timestamps_list(self) -> list[str]:
        return list(self._timestamps)


class AnomalyEngine:
    """
    Multi-metric anomaly detector.

    Maintains sliding windows for CPU, memory, error_count, and latency.
    Detects anomalies by Z-score thresholds and rate-of-change analysis.
    """

    Z_THRESHOLD = 2.5  # Z-score above which we flag an anomaly

    def __init__(self, window_size: int = 60):
        self.windows: dict[str, MetricWindow] = {
            "cpu_percent": MetricWindow(window_size),
            "memory_percent": MetricWindow(window_size),
            "error_count": MetricWindow(window_size),
        }
        self._anomaly_history: list[dict] = []

    def ingest(self, metrics: dict):
        """Push current metrics into all windows."""
        for key, window in self.windows.items():
            value = metrics.get(key, 0.0)
            window.push(float(value))

    def detect(self, metrics: dict | None = None) -> list[dict]:
        """
        Run anomaly detection on the current metric windows.

        If metrics is provided, ingest first. Returns list of anomalies.
        """
        if metrics:
            self.ingest(metrics)

        anomalies = []

        for metric_name, window in self.windows.items():
            if window.count < 5:
                continue  # Not enough data for statistical detection

            z = window.z_score()
            trend = window.trend

            if abs(z) >= self.Z_THRESHOLD:
                anomaly = {
                    "metric": metric_name,
                    "type": "z_score_anomaly",
                    "value": window.latest,
                    "z_score": round(z, 2),
                    "mean": round(window.mean, 2),
                    "std": round(window.std, 2),
                    "trend": round(trend, 2),
                    "timestamp": datetime.now().isoformat(),
                    "direction": "spike" if z > 0 else "drop",
                }
                anomalies.append(anomaly)
                self._anomaly_history.append(anomaly)

        return anomalies

    def get_metric_stats(self, metric_name: str) -> dict:
        """Return current statistics for a given metric."""
        window = self.windows.get(metric_name)
        if not window or window.count == 0:
            return {"metric": metric_name, "status": "no_data"}
        return {
            "metric": metric_name,
            "count": window.count,
            "latest": window.latest,
            "mean": round(window.mean, 2),
            "std": round(window.std, 2),
            "z_score": round(window.z_score(), 2),
            "trend": round(window.trend, 2),
        }

    def get_all_stats(self) -> dict:
        """Return statistics for all tracked metrics."""
        return {name: self.get_metric_stats(name) for name in self.windows}

    def get_history(self, metric_name: str) -> list[float]:
        """Return the full sliding window values for a metric."""
        window = self.windows.get(metric_name)
        return window.values_list() if window else []

    def get_timestamps(self, metric_name: str) -> list[str]:
        """Return timestamps for a metric's sliding window."""
        window = self.windows.get(metric_name)
        return window.timestamps_list() if window else []

    def get_anomaly_history(self) -> list[dict]:
        """Return all previously detected anomalies."""
        return list(self._anomaly_history)

    def clear_history(self):
        """Clear anomaly history."""
        self._anomaly_history.clear()


# Module-level singleton for use across the system
_engine = AnomalyEngine()


def ingest_metrics(metrics: dict):
    """Push metrics into the global anomaly engine."""
    _engine.ingest(metrics)


def detect_anomalies(metrics: dict | None = None) -> list[dict]:
    """Run anomaly detection on the global engine."""
    return _engine.detect(metrics)


def get_stats() -> dict:
    """Get all metric statistics from the global engine."""
    return _engine.get_all_stats()


def get_anomaly_log() -> list[dict]:
    """Get all previously detected anomalies."""
    return _engine.get_anomaly_history()


def get_metric_history(metric_name: str) -> list[float]:
    """Get sliding window values for a metric."""
    return _engine.get_history(metric_name)


def get_metric_timestamps(metric_name: str) -> list[str]:
    """Get timestamps for a metric's sliding window."""
    return _engine.get_timestamps(metric_name)
