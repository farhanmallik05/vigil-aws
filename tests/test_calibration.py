"""Unit tests for calibration metrics, Brier score, ECE, and CloudWatch EMF exporter."""

import pytest
from reusable_patterns.decider_guard.calibration import (
    CalibrationReport,
    apply_temperature_scaling,
    compute_brier_score,
    compute_calibration_error,
    format_cloudwatch_emf,
    generate_ascii_reliability_diagram,
)
from reusable_patterns.decider_guard.handler import DeciderGroundedGuardrail


def test_brier_score_perfect():
    """Verify Brier score is 0.0 for perfectly accurate probabilities."""
    preds = [1.0, 0.0, 1.0, 0.0]
    outcomes = [1, 0, 1, 0]
    score = compute_brier_score(preds, outcomes)
    assert score == pytest.approx(0.0, abs=1e-5)


def test_brier_score_inverted():
    """Verify Brier score is 1.0 for completely inverted probabilities."""
    preds = [1.0, 0.0]
    outcomes = [0, 1]
    score = compute_brier_score(preds, outcomes)
    assert score == pytest.approx(1.0, abs=1e-5)


def test_calibration_error_empty():
    """Verify empty lists return empty report with zero error."""
    report = compute_calibration_error([], [])
    assert report.total_samples == 0
    assert report.expected_calibration_error == 0.0
    assert report.is_well_calibrated is True


def test_calibration_error_well_calibrated():
    """Verify calibrated predictions produce low ECE."""
    # 10 samples with 90% confidence, 9 of which are 1 (90% accuracy)
    confidences = [0.90] * 10
    outcomes = [1] * 9 + [0] * 1
    report = compute_calibration_error(confidences, outcomes, num_bins=10)

    assert report.total_samples == 10
    # Mean confidence = 0.90, accuracy = 0.90 -> error = 0.0
    assert report.expected_calibration_error == pytest.approx(0.0, abs=1e-4)
    assert report.is_well_calibrated is True


def test_calibration_error_miscalibrated():
    """Verify overconfident predictions yield high ECE and trigger warning."""
    # 10 samples with 95% confidence, but all are 0 (0% accuracy)
    confidences = [0.95] * 10
    outcomes = [0] * 10
    report = compute_calibration_error(confidences, outcomes, num_bins=10)

    assert report.total_samples == 10
    assert report.expected_calibration_error > 0.50
    assert report.is_well_calibrated is False


def test_temperature_scaling():
    """Verify temperature scaling softens overconfident predictions."""
    probs = [0.95, 0.05]
    # T = 2.0 softens towards 0.5
    softened = apply_temperature_scaling(probs, temperature=2.0)
    assert softened[0] < 0.95
    assert softened[0] > 0.50
    assert softened[1] > 0.05
    assert softened[1] < 0.50

    # T = 0.5 sharpens towards extremes
    sharpened = apply_temperature_scaling(probs, temperature=0.5)
    assert sharpened[0] > 0.95
    assert sharpened[1] < 0.05


def test_ascii_reliability_diagram():
    """Verify ASCII diagram produces clean human-readable output."""
    confidences = [0.92, 0.88, 0.75, 0.45, 0.12]
    outcomes = [1, 1, 1, 0, 0]
    report = compute_calibration_error(confidences, outcomes, num_bins=5)
    diagram = generate_ascii_reliability_diagram(report)

    assert "STRANDS DECIDER 2B RELIABILITY DIAGRAM" in diagram
    assert "ECE:" in diagram
    assert "Calibration Verdict:" in diagram


def test_cloudwatch_emf_serialization():
    """Verify Amazon CloudWatch Embedded Metric Format JSON structure."""
    emf = format_cloudwatch_emf(
        namespace="AWS/Incidents",
        metric_name="DeciderLatencyMs",
        value=114.5,
        unit="Milliseconds",
        dimensions={"Model": "strands-decider-2b", "Region": "us-east-1"},
        extra_properties={"Environment": "production"},
    )

    assert "_aws" in emf
    assert emf["_aws"]["CloudWatchMetrics"][0]["Namespace"] == "AWS/Incidents"
    assert emf["_aws"]["CloudWatchMetrics"][0]["Metrics"][0]["Name"] == "DeciderLatencyMs"
    assert emf["DeciderLatencyMs"] == 114.5
    assert emf["Model"] == "strands-decider-2b"
    assert emf["Environment"] == "production"


def test_handler_emf_export():
    """Verify DeciderGroundedGuardrail exports valid EMF metrics."""
    guardrail = DeciderGroundedGuardrail()
    emf_list = guardrail.export_cloudwatch_emf()

    assert len(emf_list) == 4
    metric_names = [emf["_aws"]["CloudWatchMetrics"][0]["Metrics"][0]["Name"] for emf in emf_list]
    assert "DeciderLatencyMs" in metric_names
    assert "FastPathProceedCount" in metric_names
    assert "HumanConfirmCount" in metric_names
    assert "PolicyDenialCount" in metric_names
