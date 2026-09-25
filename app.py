"""Structra: a local-only Flask and SQLite sustainability demonstration.

Run ``python app.py`` after installing requirements.txt. All records and
calculations are illustrative, deterministic, and require no external service.
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

from flask import Flask, Response, g, jsonify, render_template, request
from werkzeug.exceptions import BadRequest, HTTPException, UnsupportedMediaType

from scoring import analyze, simulate
from shm import snapshot as shm_snapshot


BASE_DIR = Path(__file__).resolve().parent
MONTHS = tuple(f"2025-{month:02d}" for month in range(1, 13))
ACTIONS = ("hvac", "led", "solar", "water", "maintenance")
MONTH_FIELDS = (
    "electricity_kwh", "water_m3", "waste_kg", "recycled_kg",
    "maintenance_spend_aed", "maintenance_completed", "maintenance_due",
    "condition_score",
)
PROFILE_FIELDS = (
    "name", "city", "district", "building_type", "year_built",
    "floor_area_m2", "occupants", "floors", "description", "profile",
    "seed_profile", "data_source",
)
DEMO_SOURCE = "Synthetic demo data — fictional building; not a measured or certified assessment."


class InputError(ValueError):
    """An actionable validation error suitable for displaying in the UI."""


def load_samples():
    """Read the bundled, human-readable fixture without changing it."""
    with (BASE_DIR / "sample_data.json").open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, list) else payload["buildings"]


def number(value, label, minimum, maximum, *, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{label} must be a number.")
    if value < minimum or value > maximum or not math.isfinite(value):
        raise InputError(f"{label} must be between {minimum:,} and {maximum:,}.")
    if integer and int(value) != value:
        raise InputError(f"{label} must be a whole number.")
    return int(value) if integer else float(value)


def short_text(value, label, maximum, *, required=False):
    if not isinstance(value, str):
        raise InputError(f"{label} must be text.")
    value = value.strip()
    if required and not value:
        raise InputError(f"Please enter {label.lower()}.")
    if len(value) > maximum:
        raise InputError(f"{label} must be {maximum} characters or fewer.")
    return value


def validate_month(payload):
    missing = [field for field in MONTH_FIELDS if field not in payload]
    if missing:
        raise InputError("Please provide every monthly value; missing " + ", ".join(missing) + ".")
    unexpected = set(payload) - set(MONTH_FIELDS)
    if unexpected:
        raise InputError("Unrecognized monthly field: " + ", ".join(sorted(unexpected)) + ".")
    values = {}
    for field in MONTH_FIELDS:
        maximum = 100 if field == "condition_score" else 100_000 if field in ("maintenance_due", "maintenance_completed") else 100_000_000
        values[field] = number(payload[field], field.replace("_", " ").capitalize(), 0, maximum,
                               integer=field in ("maintenance_due", "maintenance_completed"))
    if values["recycled_kg"] > values["waste_kg"]:
        raise InputError("Recycled waste cannot exceed total waste.")
    if values["maintenance_completed"] > values["maintenance_due"]:
        raise InputError("Completed maintenance jobs cannot exceed jobs due.")
    return values


def validate_building(payload, samples):
    allowed = {"name", "city", "district", "building_type", "year_built", "floor_area_m2", "occupants", "floors", "description", "seed_profile"}
    if set(payload) - allowed:
        raise InputError("Unrecognized building field: " + ", ".join(sorted(set(payload) - allowed)) + ".")
    required = ("name", "city", "building_type", "year_built", "floor_area_m2", "occupants", "floors")
    for field in required:
        if field not in payload:
            raise InputError(f"Please provide {field.replace('_', ' ')}.")
    values = {
        "name": short_text(payload["name"], "Building name", 100, required=True),
        "city": short_text(payload["city"], "City", 80, required=True),
        "district": short_text(payload.get("district", ""), "District", 100),
        "description": short_text(payload.get("description", ""), "Description", 800),
        "building_type": short_text(payload["building_type"], "Building type", 40, required=True),
        "year_built": number(payload["year_built"], "Year built", 1950, datetime.now().year, integer=True),
        "floor_area_m2": number(payload["floor_area_m2"], "Floor area", 100, 1_000_000),
        "occupants": number(payload["occupants"], "Occupants", 1, 100_000, integer=True),
        "floors": number(payload["floors"], "Floors", 1, 200, integer=True),
        "seed_profile": payload.get("seed_profile", "typical"),
        "data_source": DEMO_SOURCE,
    }
    known_types = {sample["building_type"] for sample in samples}
    canonical_types = {kind.casefold(): kind for kind in known_types}
    if values["building_type"].casefold() not in canonical_types:
        raise InputError("Choose a building type: " + ", ".join(sorted(known_types)) + ".")
    values["building_type"] = canonical_types[values["building_type"].casefold()]
    if not isinstance(values["seed_profile"], str) or values["seed_profile"] not in ("typical", "efficient", "needs_attention"):
        raise InputError("Sample profile must be typical, efficient, or needs_attention.")
    values["profile"] = {"typical": "Typical operations", "efficient": "Efficient operations", "needs_attention": "Needs attention"}[values["seed_profile"]]
    return values


def generate_months(building, samples):
    """Scale a same-type 2025 fixture; preserve the UAE seasonal pattern.

    Electricity and maintenance spend scale with area; water and waste scale
    with occupants. Profile factors are applied relative to the fixture's
    stated seed profile, so choosing a typical profile always has the same
    meaning. This produces a demo dataset, never measured performance.
    """
    factors = {
        "efficient": {"electricity": .72, "water": .72, "recycling": .65, "completion": .98, "condition": 92},
        "typical": {"electricity": 1.0, "water": 1.0, "recycling": .35, "completion": .85, "condition": 78},
        "needs_attention": {"electricity": 1.3, "water": 1.3, "recycling": .15, "completion": .58, "condition": 61},
    }
    source = next(sample for sample in samples if sample["building_type"] == building["building_type"])
    selected = factors[building["seed_profile"]]
    original = factors.get(source.get("seed_profile", "typical"), factors["typical"])
    area_ratio = building["floor_area_m2"] / source["floor_area_m2"]
    occupant_ratio = building["occupants"] / source["occupants"]
    months = []
    for row in source["monthly_data"]:
        due = max(1, round(row["maintenance_due"] * area_ratio))
        waste = round(row["waste_kg"] * occupant_ratio, 2)
        months.append({
            "month": row["month"],
            "electricity_kwh": round(row["electricity_kwh"] * area_ratio * selected["electricity"] / original["electricity"], 2),
            "water_m3": round(row["water_m3"] * occupant_ratio * selected["water"] / original["water"], 2),
            "waste_kg": waste,
            "recycled_kg": round(waste * selected["recycling"], 2),
            "maintenance_spend_aed": round(row["maintenance_spend_aed"] * area_ratio, 2),
            "maintenance_due": due,
            "maintenance_completed": min(due, round(due * selected["completion"])),
            "condition_score": selected["condition"],
        })
    return months


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.environ.get("STRUCTRA_DB_PATH", str(BASE_DIR / "instance" / "structra.db")),
        MAX_CONTENT_LENGTH=64 * 1024,
        JSON_SORT_KEYS=False,
    )
    if test_config:
        app.config.update(test_config)
    app.json.sort_keys = False
    app.json.ensure_ascii = False

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @app.teardown_appcontext
    def close_db(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def insert_building(db, building, rows, *, keep_id=False):
        values = {field: building.get(field, "") for field in PROFILE_FIELDS}
        values["data_source"] = DEMO_SOURCE
        values["seed_profile"] = building.get("seed_profile", "typical")
        fields = list(PROFILE_FIELDS)
        if keep_id and building.get("id"):
            fields.insert(0, "id")
            values["id"] = building["id"]
        result = db.execute(
            f"INSERT INTO buildings ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
            [values[field] for field in fields],
        )
        building_id = result.lastrowid
        month_fields = ("building_id", "month") + MONTH_FIELDS
        db.executemany(
            f"INSERT INTO monthly_data ({', '.join(month_fields)}) VALUES ({', '.join('?' for _ in month_fields)})",
            [[building_id, row["month"]] + [row[field] for field in MONTH_FIELDS] for row in rows],
        )
        return building_id

    # Existing files are never reseeded, even if the user has removed rows.
    database_path = Path(app.config["DATABASE"])
    new_database = not database_path.exists()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db = get_db()
        db.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))
        if new_database:
            with db:
                for building in load_samples():
                    insert_building(db, building, building["monthly_data"], keep_id=True)

    def detail(building_id):
        # Flask's integer route accepts integers larger than SQLite can bind.
        if building_id > 2**63 - 1:
            from flask import abort
            abort(404, description="That demo building was not found.")
        row = get_db().execute("SELECT * FROM buildings WHERE id = ?", (building_id,)).fetchone()
        if row is None:
            from flask import abort
            abort(404, description="That demo building was not found.")
        building = dict(row)
        building["is_demo"] = True
        months = [dict(row) for row in get_db().execute(
            f"SELECT month, {', '.join(MONTH_FIELDS)} FROM monthly_data WHERE building_id = ? ORDER BY month",
            (building_id,),
        ).fetchall()]
        return {"building": building, "monthly_data": months, "analysis": analyze(building, months)}

    def json_body():
        try:
            payload = request.get_json()
        except (BadRequest, UnsupportedMediaType) as error:
            raise InputError("Send a valid JSON object with the application/json content type.") from error
        if not isinstance(payload, dict):
            raise InputError("Send a JSON object containing the form values.")
        return payload

    def structural_monitoring(building_id):
        row = get_db().execute("SELECT stage FROM shm_demo WHERE building_id = ?", (building_id,)).fetchone()
        return shm_snapshot(building_id, row["stage"] if row is not None else 0)

    def action_options(payload):
        unexpected = set(payload) - set(ACTIONS)
        if unexpected:
            raise InputError("Unrecognized simulation action: " + ", ".join(sorted(unexpected)) + ".")
        if any(not isinstance(value, bool) for value in payload.values()):
            raise InputError("Simulation actions must be true or false.")
        return {action: payload.get(action, False) for action in ACTIONS}

    @app.before_request
    def local_write_protection():
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            origin = request.headers.get("Origin")
            if origin:
                try:
                    source = urlsplit(origin)
                    target = urlsplit(request.host_url)
                except ValueError:
                    return jsonify(error="The request origin is invalid."), 403
                if (source.scheme, source.netloc) != (target.scheme, target.netloc):
                    return jsonify(error="Open Structra in this browser window before changing demo data."), 403
            if request.headers.get("Sec-Fetch-Site") == "cross-site":
                return jsonify(error="Cross-site changes are not allowed."), 403

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(InputError)
    def invalid_input(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith("/api/"):
            return jsonify(error=error.description), error.code
        return error

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/buildings")
    def buildings():
        result = []
        for row in get_db().execute("SELECT id FROM buildings ORDER BY id").fetchall():
            data = detail(row["id"])
            result.append({**data["building"], "analysis": data["analysis"]})
        return jsonify(buildings=result)

    @app.get("/api/buildings/<int:building_id>")
    def building_detail(building_id):
        return jsonify(detail(building_id))

    @app.post("/api/buildings")
    def add_building():
        samples = load_samples()
        building = validate_building(json_body(), samples)
        rows = generate_months(building, samples)
        for row in rows:
            validate_month({field: row[field] for field in MONTH_FIELDS})
        db = get_db()
        with db:
            building_id = insert_building(db, building, rows)
        return jsonify(detail(building_id)), 201

    @app.route("/api/buildings/<int:building_id>/months/<month>", methods=["GET", "PUT"])
    def monthly_record(building_id, month):
        data = detail(building_id)
        if month not in MONTHS:
            raise InputError("Choose a month from January to December 2025 (YYYY-MM).")
        existing = next((row for row in data["monthly_data"] if row["month"] == month), None)
        if existing is None:
            from flask import abort
            abort(404, description="That monthly demo record was not found.")
        if request.method == "GET":
            return jsonify(monthly_data=existing)
        values = validate_month(json_body())
        db = get_db()
        with db:
            db.execute(
                f"UPDATE monthly_data SET {', '.join(field + ' = ?' for field in MONTH_FIELDS)} WHERE building_id = ? AND month = ?",
                [values[field] for field in MONTH_FIELDS] + [building_id, month],
            )
        return jsonify(detail(building_id))

    @app.post("/api/buildings/<int:building_id>/simulate")
    def simulate_building(building_id):
        data = detail(building_id)
        options = action_options(json_body())
        return jsonify(simulate(data["building"], data["monthly_data"], options))

    @app.route("/api/buildings/<int:building_id>/shm", methods=["GET", "POST"])
    def building_shm(building_id):
        detail(building_id)  # Check existence before reading or saving a stage.
        if request.method == "POST":
            payload = json_body()
            if set(payload) != {"stage"}:
                raise InputError("Provide only the structural monitoring story stage.")
            stage = payload["stage"]
            if type(stage) is not int or stage not in range(4):
                raise InputError("Structural monitoring stage must be an integer from 0 to 3.")
            db = get_db()
            with db:
                db.execute(
                    "INSERT INTO shm_demo (building_id, stage) VALUES (?, ?) "
                    "ON CONFLICT(building_id) DO UPDATE SET stage = excluded.stage",
                    (building_id, stage),
                )
        return jsonify(structural_monitoring(building_id))

    @app.get("/api/buildings/<int:building_id>/export.csv")
    def export_csv(building_id):
        data = detail(building_id)
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=("month",) + MONTH_FIELDS)
        writer.writeheader()
        writer.writerows(data["monthly_data"])
        return Response("\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8", headers={
            "Content-Disposition": f'attachment; filename="structra-demo-building-{building_id}-2025.csv"',
        })

    @app.get("/api/buildings/<int:building_id>/passport.json")
    def export_passport(building_id):
        data = detail(building_id)
        data["structural_monitoring"] = structural_monitoring(building_id)
        data["provenance"] = {
            "source": DEMO_SOURCE,
            "period": "January–December 2025",
            "method": "Deterministic illustrative scoring rules; no external AI API or certification.",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "simulation_is_forecast": True,
        }
        response = jsonify(data)
        response.headers["Content-Disposition"] = f'attachment; filename="structra-demo-passport-{building_id}.json"'
        return response

    @app.get("/passport/<int:building_id>")
    def passport(building_id):
        data = detail(building_id)
        chosen = {}
        for action in ACTIONS:
            value = request.args.get(action, "0").lower()
            if value not in ("0", "1", "true", "false"):
                raise InputError("Passport scenario choices must be 0 or 1.")
            chosen[action] = value in ("1", "true")
        scenario = simulate(data["building"], data["monthly_data"], chosen) if any(chosen.values()) else None
        return render_template(
            "passport.html", **data,
            simulation=scenario,
            structural_monitoring=structural_monitoring(building_id),
            generated_at=datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC"),
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
