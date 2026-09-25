"""Behavior tests for the demo, using disposable databases only.

Run: python -m unittest -v
No server, browser, network service or external testing package is required.
"""

from copy import deepcopy
from contextlib import closing
import csv
import io
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest


# app.py exposes an app for Flask, so isolate even its import-time seed operation.
# The user's instance/structra.db is never opened by this test suite.
with TemporaryDirectory(prefix="structra-test-import-") as _import_directory:
    _previous_database = os.environ.get("STRUCTRA_DB_PATH")
    os.environ["STRUCTRA_DB_PATH"] = str(Path(_import_directory) / "import.db")
    try:
        from app import create_app, MONTH_FIELDS
    finally:
        if _previous_database is None:
            os.environ.pop("STRUCTRA_DB_PATH", None)
        else:
            os.environ["STRUCTRA_DB_PATH"] = _previous_database

from scoring import analyze, simulate


class StructraDemoTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="structra-test-")
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "test.db"
        self.app = create_app({"TESTING": True, "DATABASE": str(self.database)})
        self.client = self.app.test_client()

    def detail(self, building_id=1, client=None):
        response = (client or self.client).get(f"/api/buildings/{building_id}")
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def month_values(self, building_id=1):
        row = self.detail(building_id)["monthly_data"][0]
        return {field: row[field] for field in MONTH_FIELDS}

    def new_building(self, **changes):
        payload = {
            "name": "Demo Innovation Court",
            "city": "Dubai",
            "district": "Sample District",
            "building_type": "Office",
            "year_built": 2017,
            "floor_area_m2": 10000,
            "occupants": 500,
            "floors": 8,
            "description": "A fictional test property.",
            "seed_profile": "typical",
        }
        payload.update(changes)
        return payload

    def test_first_start_seeds_four_distinct_buildings_and_48_months(self):
        response = self.client.get("/api/buildings")
        self.assertEqual(response.status_code, 200)
        buildings = response.get_json()["buildings"]
        self.assertEqual(len(buildings), 4)
        self.assertEqual({b["building_type"] for b in buildings},
                         {"Office", "Residential", "Retail", "Mixed-use"})
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM monthly_data").fetchone()[0], 48)
        expected_months = [f"2025-{month:02d}" for month in range(1, 13)]
        for building in buildings:
            with self.subTest(building=building["name"]):
                data = self.detail(building["id"])
                self.assertEqual([row["month"] for row in data["monthly_data"]], expected_months)
                self.assertTrue(data["analysis"]["annual_data_complete"])
                self.assertTrue(data["building"]["is_demo"])
                self.assertIn("fictional", data["building"]["data_source"].lower())

    def test_scores_and_recommendations_are_reproducible_and_distinct(self):
        overall_scores = set()
        for building_id in range(1, 5):
            data = self.detail(building_id)
            first = analyze(data["building"], data["monthly_data"])
            again = analyze(deepcopy(data["building"]), list(reversed(data["monthly_data"])))
            self.assertEqual(first, again)
            self.assertTrue(all(0 <= score <= 100 for score in first["scores"].values()))
            self.assertGreaterEqual(len(first["recommendations"]), 5)
            self.assertTrue(all(item["reason"] and item["impact"] for item in first["recommendations"]))
            overall_scores.add(first["scores"]["overall"])
        self.assertEqual(len(overall_scores), 4)
        self.assertGreater(self.detail(3)["analysis"]["scores"]["overall"],
                           self.detail(1)["analysis"]["scores"]["overall"])

    def test_no_interventions_means_no_change_and_inputs_are_untouched(self):
        data = self.detail()
        original = deepcopy(data)
        result = simulate(data["building"], data["monthly_data"], {})
        self.assertEqual(result["baseline"]["scores"], result["projected"]["scores"])
        self.assertEqual(result["baseline"]["metrics"], result["projected"]["metrics"])
        for key, value in result["baseline"]["totals"].items():
            self.assertEqual(value, result["projected"]["totals"][key])
        self.assertEqual(result["score_change"], 0)
        self.assertTrue(all(value == 0 for value in result["savings"].values()))
        self.assertEqual(data, original)

    def test_improvement_scenarios_do_not_reduce_scores_or_mutate_saved_records(self):
        actions = ("hvac", "led", "solar", "water", "maintenance")
        for building_id in range(1, 5):
            baseline = self.detail(building_id)
            options = {}
            previous_score = baseline["analysis"]["scores"]["overall"]
            for action in actions:
                options[action] = True
                with self.subTest(building=building_id, options=options.copy()):
                    response = self.client.post(f"/api/buildings/{building_id}/simulate", json=options)
                    self.assertEqual(response.status_code, 200)
                    scenario = response.get_json()
                    self.assertGreaterEqual(scenario["projected"]["scores"]["overall"], previous_score)
                    self.assertTrue(all(value >= 0 for value in scenario["savings"].values()))
                    self.assertEqual(scenario["projected"]["scores"]["waste"],
                                     baseline["analysis"]["scores"]["waste"])
                    previous_score = scenario["projected"]["scores"]["overall"]
            self.assertEqual(self.detail(building_id), baseline)

    def test_energy_savings_compound_and_solar_preserves_physical_demand(self):
        result = self.client.post("/api/buildings/1/simulate", json={
            "hvac": True, "led": True, "solar": True,
        }).get_json()
        starting_energy = result["baseline"]["totals"]["electricity_kwh"]
        totals = result["projected"]["totals"]
        self.assertAlmostEqual(result["savings"]["electricity_kwh"] / starting_energy, 0.31184, places=6)
        self.assertGreater(totals["electricity_demand_kwh"], totals["electricity_kwh"])
        self.assertAlmostEqual(totals["electricity_demand_kwh"],
                               totals["electricity_kwh"] + totals["solar_offset_kwh"], places=2)
        self.assertEqual(result["savings"]["water_m3"], 0)

    def test_maintenance_alone_changes_health_without_claiming_resource_savings(self):
        result = self.client.post("/api/buildings/1/simulate", json={"maintenance": True}).get_json()
        self.assertGreater(result["projected"]["scores"]["health"], result["baseline"]["scores"]["health"])
        self.assertTrue(all(value == 0 for value in result["savings"].values()))
        self.assertLessEqual(result["projected"]["metrics"]["condition_score"], 100)
        self.assertLessEqual(result["projected"]["metrics"]["maintenance_completion"], 100)

    def test_add_and_monthly_edit_survive_app_restart_without_reseeding(self):
        response = self.client.post("/api/buildings", json=self.new_building())
        self.assertEqual(response.status_code, 201)
        created = response.get_json()
        building_id = created["building"]["id"]
        self.assertEqual(len(created["monthly_data"]), 12)
        values = self.month_values(building_id)
        values["electricity_kwh"] /= 2
        updated = self.client.put(f"/api/buildings/{building_id}/months/2025-01", json=values)
        self.assertEqual(updated.status_code, 200)
        self.assertLess(updated.get_json()["analysis"]["totals"]["electricity_kwh"],
                        created["analysis"]["totals"]["electricity_kwh"])
        restarted = create_app({"TESTING": True, "DATABASE": str(self.database)}).test_client()
        saved = self.detail(building_id, restarted)
        self.assertEqual(saved["building"]["name"], "Demo Innovation Court")
        self.assertEqual(saved["monthly_data"][0]["electricity_kwh"], values["electricity_kwh"])
        self.assertEqual(len(restarted.get("/api/buildings").get_json()["buildings"]), 5)

    def test_invalid_building_values_are_rejected_without_creating_rows(self):
        cases = [
            {"name": "   "}, {"name": ["Unexpected array"]},
            {"floor_area_m2": "10000"}, {"floor_area_m2": True},
            {"floor_area_m2": 0}, {"floor_area_m2": float("nan")},
            {"floor_area_m2": 10 ** 400},
            {"occupants": float("inf")}, {"occupants": 1.5},
            {"building_type": "Unknown"}, {"seed_profile": []},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                response = self.client.post("/api/buildings", json=self.new_building(**changes))
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.get_json()["error"])
        self.assertEqual(len(self.client.get("/api/buildings").get_json()["buildings"]), 4)

    def test_generated_operating_profiles_have_a_consistent_performance_order(self):
        scores = {}
        for profile in ("efficient", "typical", "needs_attention"):
            response = self.client.post("/api/buildings", json=self.new_building(seed_profile=profile))
            self.assertEqual(response.status_code, 201)
            data = response.get_json()
            scores[profile] = data["analysis"]["scores"]["overall"]
            self.assertEqual(len(data["monthly_data"]), 12)
        self.assertGreater(scores["efficient"], scores["typical"])
        self.assertGreater(scores["typical"], scores["needs_attention"])

    def test_invalid_monthly_values_leave_the_entire_baseline_intact(self):
        before = self.detail()
        base = self.month_values()
        cases = [
            {"electricity_kwh": -1}, {"water_m3": "900"},
            {"condition_score": 101}, {"condition_score": True},
            {"electricity_kwh": float("nan")}, {"water_m3": float("inf")},
            {"recycled_kg": base["waste_kg"] + 1},
            {"maintenance_completed": base["maintenance_due"] + 1},
            {"maintenance_due": 2.5}, {"unexpected": 12},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                response = self.client.put("/api/buildings/1/months/2025-01", json={**base, **changes})
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.get_json()["error"])
        missing = dict(base)
        missing.pop("water_m3")
        self.assertEqual(self.client.put("/api/buildings/1/months/2025-01", json=missing).status_code, 400)
        self.assertEqual(self.detail(), before)

    def test_bad_requests_unknown_ids_and_invalid_actions_return_clear_errors(self):
        for payload in ([True], None, "hello"):
            response = self.client.post("/api/buildings", data=json.dumps(payload), content_type="application/json")
            self.assertEqual(response.status_code, 400)
        response = self.client.post("/api/buildings", data="{not-json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        for options in ({"hvac": "false"}, {"led": 1}, {"unknown": True}):
            response = self.client.post("/api/buildings/1/simulate", json=options)
            self.assertEqual(response.status_code, 400)
            self.assertTrue(response.get_json()["error"])
        for path in ("/api/buildings/99999", "/api/buildings/9999999999999999999999999", "/api/buildings/99999/export.csv",
                     "/api/buildings/99999/passport.json", "/passport/99999"):
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.post("/api/buildings/99999/simulate", json={}).status_code, 404)
        self.assertEqual(self.client.get("/api/buildings/1/months/2025-13").status_code, 400)

    def test_csv_json_and_print_views_reflect_the_saved_building(self):
        data = self.detail()
        response = self.client.get("/api/buildings/1/export.csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response.headers["Content-Disposition"])
        records = list(csv.DictReader(io.StringIO(response.get_data().decode("utf-8-sig"))))
        self.assertEqual(len(records), 12)
        self.assertEqual(records[0]["month"], "2025-01")
        self.assertEqual(float(records[0]["electricity_kwh"]), data["monthly_data"][0]["electricity_kwh"])
        exported = self.client.get("/api/buildings/1/passport.json")
        self.assertEqual(exported.status_code, 200)
        passport = exported.get_json()
        self.assertEqual(passport["analysis"], data["analysis"])
        self.assertIn("fictional", passport["provenance"]["source"].lower())
        for path in ("/", "/passport/1", "/passport/1?hvac=1&solar=1"):
            with self.subTest(path=path):
                page = self.client.get(path)
                self.assertEqual(page.status_code, 200)
                self.assertIn("Structra", page.get_data(as_text=True))
                if path != "/":
                    self.assertIn(data["building"]["name"], page.get_data(as_text=True))

    def test_cross_site_writes_are_rejected_but_same_origin_writes_work(self):
        rejected = self.client.post("/api/buildings", json=self.new_building(),
                                    headers={"Origin": "https://unrelated.example"})
        self.assertEqual(rejected.status_code, 403)
        malformed_origin = self.client.post("/api/buildings", json=self.new_building(),
                                           headers={"Origin": "http://[invalid"})
        self.assertEqual(malformed_origin.status_code, 403)
        self.assertEqual(len(self.client.get("/api/buildings").get_json()["buildings"]), 4)
        accepted = self.client.post("/api/buildings", json=self.new_building(),
                                    headers={"Origin": "http://localhost"})
        self.assertEqual(accepted.status_code, 201)


if __name__ == "__main__":
    unittest.main(verbosity=2)
