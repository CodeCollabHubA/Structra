"""Scripted structural monitoring snapshots for the offline Structra demo.

These are invented readings and workflow records, not measurements, engineering
thresholds, diagnoses, or an assessment of a building's structural safety.
They deliberately have no connection to the sustainability scoring functions.
"""

from __future__ import annotations


STAGES = (
    ("Baseline monitoring", "Sara reviews the fictional building's vibration, crack-opening and tilt snapshots alongside its utility records. This establishes a demonstration reference, not a safety rating."),
    ("Review requested", "A scripted change appears in the monitoring snapshots. Sara requests an engineer's review and keeps the observation in the building's history. The demo does not infer a cause from the readings."),
    ("Inspection recorded", "A fictional engineer inspection has been recorded in the scenario, together with a localized repair plan. This is a scripted human decision, not a diagnosis generated from sensor values."),
    ("Follow-up recorded", "The scenario records the planned maintenance and a later monitoring snapshot. Crack opening and tilt remain above the demo reference: continued observation matters. Sara can now share monitoring history and a separate resource-efficiency plan in one passport."),
)

DISCLAIMER = (
    "Simulated readings and fictional inspection records for a hackathon story. "
    "Changes are scripted, with no engineering safety thresholds, live sensors, "
    "diagnosis or structural certification. Follow-up readings are illustrative, "
    "not guaranteed repair outcomes. Structural monitoring does not alter the "
    "separate sustainability score."
)


def snapshot(building_id: int, stage: int = 0) -> dict:
    """Return a deterministic twelve-point snapshot at a selected story stage."""
    if type(stage) is not int or stage not in range(4):
        raise ValueError("Stage must be an integer from 0 to 3.")
    variant = (building_id - 1) % 4
    channels = []
    definitions = (
        ("vibration", "Vibration baseline ratio", "Plant room slab · demo point V1", "× baseline", 1.0, 1.38 + variant * .02, 1.08 + variant * .01, 2),
        ("crack", "Crack opening", "Facade joint · demo gauge C1", "mm", .18 + variant * .01, .32 + variant * .01, .29 + variant * .01, 2),
        ("tilt", "Tilt", "Roof reference · demo point T1", "°", .04 + variant * .005, .07 + variant * .005, .06 + variant * .005, 3),
    )
    # The ratios below draw illustrative traces. They never trigger or clear an
    # engineering alarm. A presenter explicitly selects each scripted stage.
    for channel_id, label, location, unit, baseline, changed, followup, places in definitions:
        baseline = round(baseline, places)
        changed = round(changed, places)
        followup = round(followup, places)
        current = baseline if stage == 0 else changed if stage in (1, 2) else followup
        if stage == 0:
            history = [round(baseline * factor, places) for factor in (1, .99, 1.01, 1, 1.02, 1, .99, 1.01, 1, 1.01, .99, 1)]
        elif stage in (1, 2):
            history = [baseline] * 5 + [round(baseline + (changed - baseline) * factor, places) for factor in (.12, .25, .42, .58, .76, .9, 1)]
        else:
            history = [baseline] * 3 + [round(baseline + (changed - baseline) * factor, places) for factor in (.25, .55, .8, 1)]
            history += [round(changed + (followup - changed) * factor, places) for factor in (.15, .4, .65, .85, 1)]
        channels.append({
            "id": channel_id, "label": label, "location": location,
            "unit": unit, "baseline": baseline, "current": current,
            "history": history,
        })
    event_details = (
        ("Monitoring reference saved", "Twelve illustrative snapshots provide a demo reference; they are not live sensor readings."),
        ("Engineer review requested", "The presenter triggers this observation flag. Actual significance and next steps would require engineering review."),
        ("Fictional inspection and repair plan recorded", "Scripted engineer decision: a localized repair plan is entered after a fictional inspection; the app has not diagnosed a defect."),
        ("Demo maintenance and follow-up recorded", "The scenario records the planned work and later observations. The readings do not establish repair effectiveness or certify safety."),
    )
    return {
        "building_id": building_id,
        "stage": stage,
        "stage_label": STAGES[stage][0],
        "story": STAGES[stage][1],
        "channels": channels,
        "events": [{"title": title, "note": note, "status": "recorded" if index <= stage else "pending"}
                   for index, (title, note) in enumerate(event_details)],
        "disclaimer": DISCLAIMER,
    }
