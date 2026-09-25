"""Transparent, deterministic demonstration model. No external services required.

All benchmarks, factors and savings assumptions below are invented demo settings,
not UAE tariffs, engineering assessments, verified emissions or certifications.
"""

from copy import deepcopy
from datetime import datetime
import math


ELECTRICITY_COST_AED_PER_KWH = 0.38
WATER_COST_AED_PER_M3 = 8.0
GRID_KG_CO2E_PER_KWH = 0.40
WEIGHTS = {"energy": 0.35, "water": 0.25, "waste": 0.20, "health": 0.20}
# An intensity at/below the first value scores 100; at/above the second scores 0.
BENCHMARKS = {
    "Office": {"energy": (110, 360), "water": (0.25, 1.10)},
    "Residential": {"energy": (90, 260), "water": (0.80, 2.80)},
    "Retail": {"energy": (140, 440), "water": (0.35, 1.30)},
    "Mixed-use": {"energy": (115, 330), "water": (0.60, 2.00)},
}
OPTION_NAMES = ("hvac", "led", "solar", "water", "maintenance")
SUM_FIELDS = (
    "electricity_kwh", "water_m3", "waste_kg", "recycled_kg",
    "maintenance_spend_aed", "maintenance_completed", "maintenance_due",
)


def _number(value, default=0):
    """Keep imperfect imported inputs finite and non-negative."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return max(0.0, result) if math.isfinite(result) else float(default)


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def _intensity_score(value, bounds):
    good, poor = bounds
    return _clamp(100 * (poor - value) / (poor - good))


def _clean_rows(rows):
    clean = []
    seen = set()
    for source in rows or []:
        row = dict(source)
        month = str(row.get("month", ""))
        try:
            parsed = datetime.strptime(month, "%Y-%m")
        except ValueError as exc:
            raise ValueError("Each monthly record needs a month in YYYY-MM format.") from exc
        if parsed.strftime("%Y-%m") != month:
            raise ValueError("Each monthly record needs a month in YYYY-MM format.")
        if month in seen:
            raise ValueError("Monthly records must not repeat a month.")
        seen.add(month)
        row["month"] = month
        for field in SUM_FIELDS:
            row[field] = _number(row.get(field))
        row["recycled_kg"] = min(row["recycled_kg"], row["waste_kg"])
        row["maintenance_completed"] = min(row["maintenance_completed"], row["maintenance_due"])
        row["condition_score"] = _clamp(_number(row.get("condition_score")))
        clean.append(row)
    return sorted(clean, key=lambda row: row["month"])


def _rating(score):
    return "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "E"


def analyze(building, monthly_data):
    """Calculate period totals, annualized intensities and an illustrative score.

    This function never writes to the supplied building or monthly records.
    A partial period is annualized with 12 / month count and clearly flagged.
    """
    building = dict(building)
    rows = _clean_rows(monthly_data)
    count = len(rows)
    area = _number(building.get("floor_area_m2"))
    has_data = bool(count and area > 0)
    factor = 12 / count if count else 0
    kind = building.get("building_type", "Office")
    benchmark = BENCHMARKS.get(kind, BENCHMARKS["Office"])
    totals = {field: sum(row[field] for row in rows) for field in SUM_FIELDS}
    totals["carbon_tonnes"] = totals["electricity_kwh"] * GRID_KG_CO2E_PER_KWH / 1000
    totals["utility_cost_aed"] = (
        totals["electricity_kwh"] * ELECTRICITY_COST_AED_PER_KWH
        + totals["water_m3"] * WATER_COST_AED_PER_M3
    )
    energy = totals["electricity_kwh"] * factor / area if area else 0
    water = totals["water_m3"] * factor / area if area else 0
    recycling = 100 * totals["recycled_kg"] / totals["waste_kg"] if totals["waste_kg"] else 0
    completion = (100 * totals["maintenance_completed"] / totals["maintenance_due"]
                  if totals["maintenance_due"] else (100 if count else 0))
    condition = sum(row["condition_score"] for row in rows) / count if count else 0
    metrics = {
        "energy_intensity": round(energy, 1),
        "water_intensity": round(water, 3),
        "recycling_rate": round(recycling, 1),
        "maintenance_completion": round(completion, 1),
        "condition_score": round(condition, 1),
    }
    raw_scores = {
        "energy": _intensity_score(energy, benchmark["energy"]),
        "water": _intensity_score(water, benchmark["water"]),
        "waste": _clamp(recycling / 70 * 100),
        "health": _clamp(condition * 0.65 + completion * 0.35),
    } if has_data else dict.fromkeys(WEIGHTS, 0)
    scores = {key: round(value) for key, value in raw_scores.items()}
    scores["overall"] = round(sum(raw_scores[key] * weight for key, weight in WEIGHTS.items()))
    months = [row["month"] for row in rows]
    annual_complete = (count == 12 and months[0][-2:] == "01" and months[-1][-2:] == "12"
                       and len({month[:4] for month in months}) == 1)
    period = (f"{datetime.strptime(months[0], '%Y-%m').strftime('%b %Y')} – "
              f"{datetime.strptime(months[-1], '%Y-%m').strftime('%b %Y')}") if count else "No monthly data"
    weakest = min(raw_scores, key=raw_scores.get) if has_data else None
    names = {"energy": "grid electricity demand", "water": "water consumption",
             "waste": "waste diversion", "health": "asset care"}
    insights = (f"The largest improvement opportunity is {names[weakest]}. "
                "Use the simulator to explore how practical actions change this demo passport."
                if has_data else "Add monthly records and a valid floor area to calculate a demo passport.")
    if count and not annual_complete:
        insights += f" This is a partial or non-calendar period; intensities use a {factor:.2f}× annualization factor."
    recommendations = _recommendations(metrics, scores, totals) if has_data else []
    return {
        "totals": {key: round(value, 2) for key, value in totals.items()},
        "metrics": metrics,
        "scores": scores,
        "rating": _rating(scores["overall"]) if has_data else "—",
        "recommendations": recommendations,
        "insights": insights,
        "annual_data_complete": annual_complete,
        "has_data": has_data,
        "month_count": count,
        "period": period,
        "methodology": {
            "label": "Illustrative demo model — not a building certification",
            "weights": WEIGHTS.copy(),
            "energy_benchmark": list(benchmark["energy"]),
            "water_benchmark": list(benchmark["water"]),
            "energy_unit": "grid kWh/m²/year",
            "water_unit": "m³/m²/year",
            "intensity_formula": "score = clamp(100 × (poor − intensity) / (poor − good), 0, 100)",
            "waste_formula": "score = clamp(recycled share (%) / 70 × 100, 0, 100)",
            "health_formula": "score = 65% average condition + 35% maintenance completion",
            "overall_formula": "35% energy + 25% water + 20% waste + 20% health, using unrounded component scores",
            "rating_bands": "A ≥ 85; B ≥ 70; C ≥ 55; D ≥ 40; E < 40",
            "annualization_factor": round(factor, 4),
            "electricity_cost_aed_per_kwh": ELECTRICITY_COST_AED_PER_KWH,
            "water_cost_aed_per_m3": WATER_COST_AED_PER_M3,
            "grid_kg_co2e_per_kwh": GRID_KG_CO2E_PER_KWH,
            "scope": "Carbon covers purchased grid electricity only. Water, waste, refrigerants, embodied carbon and on-site fuels are excluded.",
            "limitations": "Invented benchmarks and factors for demonstration; not local tariffs, measured emissions, an engineering assessment or financial advice. No lifecycle cost, capital expenditure or payback is calculated.",
            "data_note": "Monthly records are fictional sample data. Zero waste gives a zero diversion score; no maintenance due gives 100% completion. Partial periods are annualized without seasonal correction.",
        },
    }


def _recommendations(metrics, scores, totals):
    def priority(score):
        return "High" if score < 55 else "Medium" if score < 80 else "Low"

    energy = totals["electricity_kwh"]
    water = totals["water_m3"]
    records = [
        {"id": "hvac", "action_id": "hvac", "title": "Optimize cooling schedules",
         "reason": f"Grid electricity intensity is {metrics['energy_intensity']:,.0f} kWh/m²/year. Review setpoints, run-hours and cooling controls.",
         "impact": f"Demo assumption: 12% less electricity demand; {energy * .12:,.0f} kWh per displayed period if used alone.",
         "priority": priority(scores["energy"])},
        {"id": "led", "action_id": "led", "title": "Upgrade common-area lighting",
         "reason": "Lighting controls and LEDs offer a second operational efficiency scenario; no fixture audit has been performed.",
         "impact": f"Demo assumption: 8% of demand remaining after cooling optimization; {energy * .08:,.0f} kWh if used alone.",
         "priority": priority(scores["energy"])},
        {"id": "solar", "action_id": "solar", "title": "Explore rooftop solar",
         "reason": "Model partial on-site generation as a reduction in purchased grid electricity. Roof capacity has not been assessed.",
         "impact": "Demo assumption: solar offsets 15% of remaining grid electricity after demand savings; physical demand is unchanged.",
         "priority": "Medium"},
        {"id": "water", "action_id": "water", "title": "Investigate and repair water leaks",
         "reason": f"Water intensity is {metrics['water_intensity']:.2f} m³/m²/year. The demo models a leak-repair opportunity; a leak is not confirmed.",
         "impact": f"Demo assumption: 18% lower water use, or {water * .18:,.0f} m³ per displayed period.",
         "priority": priority(scores["water"])},
        {"id": "maintenance", "action_id": "maintenance", "title": "Strengthen preventive maintenance",
         "reason": f"Completed {metrics['maintenance_completion']:.0f}% of scheduled tasks; average recorded condition is {metrics['condition_score']:.0f}/100.",
         "impact": "Demo assumption: close half the outstanding tasks and add up to 8 condition points; no energy, money or carbon savings assigned.",
         "priority": priority(scores["health"])},
        {"id": "waste", "action_id": None, "title": "Improve waste separation",
         "reason": f"{metrics['recycling_rate']:.0f}% of recorded waste is recycled. Clearer sorting stations and a collection audit can identify opportunities.",
         "impact": "Operational recommendation only. Waste improvements are not modeled by the five simulator controls.",
         "priority": priority(scores["waste"])},
    ]
    rank = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(records, key=lambda item: rank[item["priority"]])


def simulate(building, rows, options=None):
    """Apply reversible what-if changes to copies of monthly records."""
    options = options or {}
    selected = {key: options.get(key) is True for key in OPTION_NAMES}
    baseline = analyze(building, rows)
    projected_rows = deepcopy(_clean_rows(rows))
    gross_demand = 0.0
    solar_offset = 0.0
    for row in projected_rows:
        demand = row["electricity_kwh"]
        if selected["hvac"]:
            demand *= 0.88
        if selected["led"]:
            demand *= 0.92
        offset = demand * 0.15 if selected["solar"] else 0
        gross_demand += demand
        solar_offset += offset
        row["electricity_kwh"] = demand - offset
        if selected["water"]:
            row["water_m3"] *= 0.82
        if selected["maintenance"]:
            gap = row["maintenance_due"] - row["maintenance_completed"]
            row["maintenance_completed"] += math.ceil(gap * .5)
            row["condition_score"] = min(100, row["condition_score"] + 8)
    projected = analyze(building, projected_rows)
    projected["totals"]["electricity_demand_kwh"] = round(gross_demand, 2)
    projected["totals"]["solar_offset_kwh"] = round(solar_offset, 2)
    savings = {
        key: round(max(0, baseline["totals"][field] - projected["totals"][field]), 2)
        for key, field in (("electricity_kwh", "electricity_kwh"), ("water_m3", "water_m3"),
                           ("carbon_tonnes", "carbon_tonnes"), ("cost_aed", "utility_cost_aed"))
    }
    assumptions = [
        "Illustrative what-if scenario, not an engineering forecast. Original records are unchanged.",
        "Savings cover the displayed data period; they are annual only when 12 calendar months are present.",
        "Demand reductions apply sequentially: cooling −12%, then LEDs −8% of remaining demand. They are not added together.",
        "Solar offsets 15% of remaining grid imports. Solar does not reduce physical electricity demand; the energy score measures grid intensity.",
        "Leak repair assumes an 18% water reduction; the input data does not establish that a leak exists.",
        "Preventive maintenance closes half of each month's outstanding tasks, rounded up, and improves condition by up to 8 points (maximum 100). No monetary or carbon saving is assigned.",
        "Illustrative factors: AED 0.38/kWh, AED 8/m³ and 0.40 kg CO₂e/grid kWh. These are invented demo inputs, not current tariffs or verified emissions factors.",
        "Capital costs, solar feasibility, payback, waste changes and embodied carbon are not modeled.",
    ]
    return {
        "baseline": baseline,
        "projected": projected,
        "savings": savings,
        "score_change": projected["scores"]["overall"] - baseline["scores"]["overall"],
        "assumptions": assumptions,
        "options": selected,
    }
