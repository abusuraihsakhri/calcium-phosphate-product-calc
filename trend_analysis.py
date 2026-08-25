#!/usr/bin/env python3
"""
Calcium-Phosphate Product Trend Analysis for Ca PO4 Product Calculator.
Tracks temporal trends in Ca x PO4 product to predict calcification risk.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CaPO4Measurement:
    """Single Ca x PO4 measurement."""
    date: str
    calcium_mg_dl: float
    phosphate_mg_dl: float
    product: float = 0.0
    pth_pg_ml: float = 0.0
    vitamin_d_ng_ml: float = 0.0


def analyze_caPO4_trend(measurements: List[CaPO4Measurement]) -> Dict[str, Any]:
    """Analyze temporal trends in Ca x PO4 product."""
    if not measurements:
        return {"error": "No measurements provided"}

    for m in measurements:
        m.product = m.calcium_mg_dl * m.phosphate_mg_dl

    products = [m.product for m in measurements]
    dates = [m.date for m in measurements]

    if len(products) >= 2:
        slope = (products[-1] - products[0]) / max(len(products) - 1, 1)
    else:
        slope = 0.0

    avg_product = sum(products) / len(products)
    max_product = max(products)
    latest = products[-1]

    if latest > 70:
        risk_level = "VERY_HIGH"
        recommendation = "Urgent phosphate binder review. Consider dialysis optimization."
    elif latest > 55:
        risk_level = "HIGH"
        recommendation = "Intensify phosphate management. Review diet and binders."
    elif latest > 45:
        risk_level = "MODERATE"
        recommendation = "Optimize phosphate control. Consider dietary counseling."
    else:
        risk_level = "LOW"
        recommendation = "Continue current management. Monitor as scheduled."

    pth_values = [m.pth_pg_ml for m in measurements if m.pth_pg_ml > 0]
    pth_trend = "stable"
    if len(pth_values) >= 2:
        pth_change = pth_values[-1] - pth_values[0]
        if pth_change > 50:
            pth_trend = "rising"
        elif pth_change < -50:
            pth_trend = "falling"

    return {
        "measurement_count": len(measurements),
        "latest_product": round(latest, 1),
        "average_product": round(avg_product, 1),
        "max_product": round(max_product, 1),
        "trend_slope": round(slope, 2),
        "trend_direction": "rising" if slope > 1.0 else "falling" if slope < -1.0 else "stable",
        "risk_level": risk_level,
        "recommendation": recommendation,
        "pth_trend": pth_trend,
        "calcification_risk_pct": min(95.0, latest * 1.2),
        "dates": dates,
    }


class CaPO4TrendAgent:
    """Sub-agent for Ca x PO4 trend analysis."""

    def __init__(self):
        self.agent_name = "CaPO4TrendAgent"

    def evaluate(self, measurements: List[CaPO4Measurement]) -> Dict[str, Any]:
        """Evaluate Ca x PO4 trend."""
        result = analyze_caPO4_trend(measurements)
        alerts = []

        if "error" in result:
            return {"trend_result": result, "alerts": [{"type": "NO_DATA", "severity": "ERROR",
                    "message": result["error"], "recommendation": "Provide measurement data."}]}

        if result["risk_level"] in ("VERY_HIGH", "HIGH"):
            alerts.append({
                "type": "HIGH_CAPO4_PRODUCT", "severity": "WARNING",
                "message": f"Ca x PO4 product {result['latest_product']:.1f} ({result['risk_level']} risk).",
                "recommendation": result["recommendation"]
            })

        if result["trend_direction"] == "rising" and result["trend_slope"] > 5:
            alerts.append({
                "type": "RISING_TREND", "severity": "WARNING",
                "message": f"Rising trend detected (slope: {result['trend_slope']:.2f}).",
                "recommendation": "Intensify phosphate management. Consider treatment change."
            })

        return {"trend_result": result, "alerts": alerts}
