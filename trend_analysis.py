#!/usr/bin/env python3
"""Calcium-phosphate product trend arithmetic without risk prediction."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class CaPO4Measurement:
    date: str
    calcium_mg_dl: float
    phosphate_mg_dl: float
    product: float = 0.0
    pth_pg_ml: float = 0.0
    vitamin_d_ng_ml: float = 0.0


def analyze_caPO4_trend(measurements: List[CaPO4Measurement]) -> Dict[str, Any]:
    if not measurements:
        return {"error": "No measurements provided"}

    for measurement in measurements:
        if measurement.calcium_mg_dl <= 0 or measurement.phosphate_mg_dl <= 0:
            raise ValueError("calcium and phosphate must be positive")
        measurement.product = measurement.calcium_mg_dl * measurement.phosphate_mg_dl

    products = [measurement.product for measurement in measurements]
    slope = (products[-1] - products[0]) / max(len(products) - 1, 1)
    pth_values = [m.pth_pg_ml for m in measurements if m.pth_pg_ml > 0]

    pth_trend = "stable"
    if len(pth_values) >= 2:
        change = pth_values[-1] - pth_values[0]
        if change > 50:
            pth_trend = "rising"
        elif change < -50:
            pth_trend = "falling"

    return {
        "measurement_count": len(measurements),
        "latest_product": round(products[-1], 2),
        "average_product": round(sum(products) / len(products), 2),
        "max_product": round(max(products), 2),
        "trend_slope": round(slope, 2),
        "trend_direction": "rising" if slope > 1 else "falling" if slope < -1 else "stable",
        "risk_level": "not_estimated",
        "recommendation": None,
        "pth_trend": pth_trend,
        "calcification_risk_pct": None,
        "dates": [m.date for m in measurements],
        "interpretation_note": (
            "Trend arithmetic is descriptive. Clinical decisions should use serial calcium, "
            "phosphate, PTH, and the broader CKD-MBD context."
        ),
    }


class CaPO4TrendAgent:
    def __init__(self) -> None:
        self.agent_name = "CaPO4TrendAgent"

    def evaluate(self, measurements: List[CaPO4Measurement]) -> Dict[str, Any]:
        return {"trend_result": analyze_caPO4_trend(measurements), "alerts": []}
