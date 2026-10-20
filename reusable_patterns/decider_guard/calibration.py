"""Statistical calibration and reliability diagnostics for Strands Decider 2B.

Provides production-grade calibration evaluation:
- Expected Calibration Error (ECE)
- Maximum Calibration Error (MCE)
- Brier Score
- Reliability Diagram Data Generation
- Temperature Scaling for logit recalibration
- Amazon CloudWatch Embedded Metric Format (EMF) serialization
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CalibrationBin:
    """Represents a single confidence bin in a reliability diagram."""
    bin_index: int
    bin_lower: float
    bin_upper: float
    sample_count: int
    mean_confidence: float
    empirical_accuracy: float
    calibration_error: float


@dataclass
class CalibrationReport:
    """Comprehensive statistical calibration assessment report."""
    total_samples: int
    expected_calibration_error: float
    maximum_calibration_error: float
    brier_score: float
    is_well_calibrated: bool  # True if ECE < 0.10
    bins: List[CalibrationBin]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_samples": self.total_samples,
            "expected_calibration_error": round(self.expected_calibration_error, 4),
            "maximum_calibration_error": round(self.maximum_calibration_error, 4),
            "brier_score": round(self.brier_score, 4),
            "is_well_calibrated": self.is_well_calibrated,
            "bins": [
                {
                    "bin": b.bin_index,
                    "range": [round(b.bin_lower, 2), round(b.bin_upper, 2)],
                    "count": b.sample_count,
                    "mean_conf": round(b.mean_confidence, 4),
                    "accuracy": round(b.empirical_accuracy, 4),
                    "error": round(b.calibration_error, 4),
                }
                for b in self.bins
                if b.sample_count > 0
            ],
        }


def compute_brier_score(predictions: List[float], outcomes: List[int]) -> float:
    """Computes standard Brier Score: (1/N) * sum((pred_i - outcome_i)^2).
    
    Ranges from 0.0 (perfect probabilistic prediction) to 1.0 (completely inverted).
    """
    if not predictions or not outcomes:
        return 0.0
    if len(predictions) != len(outcomes):
        raise ValueError(f"Predictions ({len(predictions)}) and outcomes ({len(outcomes)}) must match in length.")

    n = len(predictions)
    total_squared_diff = sum((float(p) - float(y)) ** 2 for p, y in zip(predictions, outcomes))
    return total_squared_diff / n


def compute_calibration_error(
    confidences: List[float],
    outcomes: List[int],
    num_bins: int = 10,
) -> CalibrationReport:
    """Computes Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).

    Args:
        confidences: Predicted probabilities in range [0.0, 1.0].
        outcomes: Binary ground truth labels (1 = positive/correct, 0 = negative/incorrect).
        num_bins: Number of equal-width bins across [0.0, 1.0]. Default: 10.

    Returns:
        CalibrationReport containing ECE, MCE, Brier Score, and per-bin diagnostics.
    """
    if not confidences or not outcomes:
        return CalibrationReport(
            total_samples=0,
            expected_calibration_error=0.0,
            maximum_calibration_error=0.0,
            brier_score=0.0,
            is_well_calibrated=True,
            bins=[],
        )

    if len(confidences) != len(outcomes):
        raise ValueError("Confidences and outcomes must have the same length.")

    n = len(confidences)
    bin_width = 1.0 / num_bins
    bins_data: List[CalibrationBin] = []

    total_weighted_ece = 0.0
    max_ce = 0.0

    for i in range(num_bins):
        b_lower = i * bin_width
        b_upper = (i + 1) * bin_width

        # Collect items in current bin [b_lower, b_upper) or [b_lower, b_upper] for last bin
        bin_samples: List[Tuple[float, int]] = []
        for c, y in zip(confidences, outcomes):
            if i == num_bins - 1:
                if b_lower <= c <= b_upper:
                    bin_samples.append((c, y))
            else:
                if b_lower <= c < b_upper:
                    bin_samples.append((c, y))

        sample_count = len(bin_samples)
        if sample_count > 0:
            mean_conf = sum(c for c, _ in bin_samples) / sample_count
            accuracy = sum(y for _, y in bin_samples) / sample_count
            cal_err = abs(accuracy - mean_conf)
            total_weighted_ece += (sample_count / n) * cal_err
            if cal_err > max_ce:
                max_ce = cal_err
        else:
            mean_conf = (b_lower + b_upper) / 2.0
            accuracy = 0.0
            cal_err = 0.0

        bins_data.append(
            CalibrationBin(
                bin_index=i + 1,
                bin_lower=b_lower,
                bin_upper=b_upper,
                sample_count=sample_count,
                mean_confidence=mean_conf,
                empirical_accuracy=accuracy,
                calibration_error=cal_err,
            )
        )

    brier = compute_brier_score(confidences, outcomes)

    return CalibrationReport(
        total_samples=n,
        expected_calibration_error=total_weighted_ece,
        maximum_calibration_error=max_ce,
        brier_score=brier,
        is_well_calibrated=total_weighted_ece < 0.10,
        bins=bins_data,
    )


def apply_temperature_scaling(probabilities: List[float], temperature: float) -> List[float]:
    """Applies temperature scaling to probabilities via logit scaling.
    
    p -> logit(p) / T -> sigmoid(logit / T).
    When T > 1, softens high-confidence peaks (defuses overconfidence).
    When T < 1, sharpens distribution.
    """
    if temperature <= 0:
        raise ValueError("Temperature must be strictly positive.")

    scaled_probs: List[float] = []
    eps = 1e-7

    for p in probabilities:
        # Clamp probability for numeric stability
        p_clamped = max(eps, min(1.0 - eps, p))
        logit = math.log(p_clamped / (1.0 - p_clamped))
        scaled_logit = logit / temperature
        # Sigmoid
        new_p = 1.0 / (1.0 + math.exp(-scaled_logit))
        scaled_probs.append(new_p)

    return scaled_probs


def generate_ascii_reliability_diagram(report: CalibrationReport) -> str:
    """Generates an ASCII visualization of the reliability calibration diagram."""
    lines = [
        "===========================================================",
        f" STRANDS DECIDER 2B RELIABILITY DIAGRAM (N={report.total_samples})",
        f" ECE: {report.expected_calibration_error:.4f} | MCE: {report.maximum_calibration_error:.4f} | Brier: {report.brier_score:.4f}",
        "===========================================================",
        "Bin Range    Count   MeanConf  EmpiricalAcc  Calibration Gap",
        "-----------------------------------------------------------",
    ]

    for b in report.bins:
        if b.sample_count == 0:
            continue
        bar_len = int(round(b.calibration_error * 20))
        gap_bar = "#" * bar_len
        sign = "+" if b.empirical_accuracy >= b.mean_confidence else "-"
        lines.append(
            f"[{b.bin_lower:.2f}-{b.bin_upper:.2f}]  "
            f"{b.sample_count:5d}   "
            f"{b.mean_confidence:.3f}     "
            f"{b.empirical_accuracy:.3f}         "
            f"{sign}{b.calibration_error:.3f} {gap_bar}"
        )

    lines.append("-----------------------------------------------------------")
    verdict = "[PASS] Well-calibrated (ECE < 0.10)" if report.is_well_calibrated else "[WARN] Recalibration recommended (ECE >= 0.10)"
    lines.append(f"Calibration Verdict: {verdict}")
    lines.append("===========================================================")
    return "\n".join(lines)


def format_cloudwatch_emf(
    namespace: str,
    metric_name: str,
    value: float,
    unit: str,
    dimensions: Dict[str, str],
    extra_properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generates an AWS CloudWatch Embedded Metric Format (EMF) compliant JSON object.
    
    Allows sub-second telemetry to flow straight into CloudWatch Metrics & Alarms
    without calling the PutMetricData API.
    """
    import time

    timestamp_ms = int(time.time() * 1000)
    dimension_keys = list(dimensions.keys())

    emf_payload: Dict[str, Any] = {
        "_aws": {
            "Timestamp": timestamp_ms,
            "CloudWatchMetrics": [
                {
                    "Namespace": namespace,
                    "Dimensions": [dimension_keys],
                    "Metrics": [
                        {
                            "Name": metric_name,
                            "Unit": unit,
                        }
                    ],
                }
            ],
        },
        metric_name: value,
    }

    # Add dimensions to root
    for k, v in dimensions.items():
        emf_payload[k] = v

    # Add optional context properties
    if extra_properties:
        for k, v in extra_properties.items():
            emf_payload[k] = v

    return emf_payload
