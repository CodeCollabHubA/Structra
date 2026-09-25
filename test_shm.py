"""Structural demo workflow checks using disposable databases only."""

from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


with TemporaryDirectory(prefix="structra-shm-import-") as _import_directory:
    _previous_database = os.environ.get("STRUCTRA_DB_PATH")
    os.environ["STRUCTRA_DB_PATH"] = str(Path(_import_directory) / "import.db")
    try:
        from app import create_app
    finally:
        if _previous_database is None:
            os.environ.pop("STRUCTRA_DB_PATH", None)
        else:
            os.environ["STRUCTRA_DB_PATH"] = _previous_database


class StructuralMonitoringDemoTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="structra-shm-test-")
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "test.db"
        self.config = {"TESTING": True, "DATABASE": str(self.database)}
        self.client = create_app(self.config).test_client()

    def test_baseline_is_deterministic_and_get_does_not_write(self):
        first = self.client.get("/api/buildings/1/shm")
        self.assertEqual(first.status_code, 200)
        data = first.get_json()
        self.assertEqual(data["stage"], 0)
        self.assertEqual(data, self.client.get("/api/buildings/1/shm").get_json())
        self.assertEqual({channel["id"] for channel in data["channels"]}, {"vibration", "crack", "tilt"})
        self.assertTrue(all(len(channel["history"]) == 12 for channel in data["channels"]))
        self.assertTrue(all(channel["baseline"] == channel["current"] == channel["history"][-1]
                            for channel in data["channels"]))
        self.assertIn("Simulated", data["disclaimer"])
        self.assertNotIn("score", data)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM shm_demo").fetchone()[0], 0)

    def test_stage_persists_per_building_and_can_reset(self):
        response = self.client.post("/api/buildings/1/shm", json={"stage": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["stage_label"], "Inspection recorded")
        restarted = create_app(self.config).test_client()
        self.assertEqual(restarted.get("/api/buildings/1/shm").get_json(), response.get_json())
        self.assertEqual(restarted.get("/api/buildings/2/shm").get_json()["stage"], 0)
        reset = restarted.post("/api/buildings/1/shm", json={"stage": 0})
        self.assertEqual(reset.status_code, 200)
        self.assertEqual(reset.get_json()["stage"], 0)

    def test_stages_preserve_observation_during_inspection_and_show_partial_followup(self):
        snapshots = [self.client.post("/api/buildings/1/shm", json={"stage": stage}).get_json()
                     for stage in range(4)]
        self.assertEqual(snapshots[1]["channels"], snapshots[2]["channels"])
        self.assertIn("scripted human decision", snapshots[2]["story"])
        for before, changed, followed in zip(snapshots[0]["channels"], snapshots[1]["channels"], snapshots[3]["channels"]):
            self.assertGreater(changed["current"], before["current"])
            self.assertLess(followed["current"], changed["current"])
            self.assertGreater(followed["current"], before["current"])
            self.assertEqual(followed["history"][-1], followed["current"])
        for stage, snapshot in enumerate(snapshots):
            self.assertEqual(sum(event["status"] == "recorded" for event in snapshot["events"]), stage + 1)

    def test_structural_workflow_and_sustainability_are_independent(self):
        baseline = self.client.get("/api/buildings/1").get_json()
        for stage in (1, 2, 3, 0):
            self.assertEqual(self.client.post("/api/buildings/1/shm", json={"stage": stage}).status_code, 200)
            self.assertEqual(self.client.get("/api/buildings/1").get_json(), baseline)
        self.client.post("/api/buildings/1/shm", json={"stage": 1})
        observed = self.client.get("/api/buildings/1/shm").get_json()
        self.assertEqual(self.client.post("/api/buildings/1/simulate", json={"maintenance": True, "hvac": True}).status_code, 200)
        self.assertEqual(self.client.get("/api/buildings/1/shm").get_json(), observed)

    def test_invalid_stages_or_payloads_leave_state_unchanged(self):
        self.client.post("/api/buildings/1/shm", json={"stage": 1})
        cases = [{}, {"stage": 2, "unexpected": True}]
        cases += [{"stage": value} for value in (True, False, 1.0, 1.5, "1", None, [], {}, -1, 4, 10 ** 50)]
        cases += [[], "stage", None]
        for payload in cases:
            with self.subTest(payload=payload):
                response = self.client.post("/api/buildings/1/shm", data=json.dumps(payload), content_type="application/json")
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.get_json()["error"])
        self.assertEqual(self.client.post("/api/buildings/1/shm", data="{invalid", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.get("/api/buildings/1/shm").get_json()["stage"], 1)
        for building_id in (99999, 10 ** 50):
            self.assertEqual(self.client.get(f"/api/buildings/{building_id}/shm").status_code, 404)
            self.assertEqual(self.client.post(f"/api/buildings/{building_id}/shm", json={"stage": 1}).status_code, 404)

    def test_new_building_has_baseline_and_foreign_key_cascade(self):
        source = self.client.get("/api/buildings/1").get_json()["building"]
        keys = ("name", "city", "district", "building_type", "year_built", "floor_area_m2", "occupants", "floors", "description", "seed_profile")
        payload = {key: source[key] for key in keys}
        payload["name"] = "Fictional SHM Test Building"
        created = self.client.post("/api/buildings", json=payload)
        self.assertEqual(created.status_code, 201)
        building_id = created.get_json()["building"]["id"]
        self.assertEqual(self.client.get(f"/api/buildings/{building_id}/shm").get_json()["stage"], 0)
        self.client.post(f"/api/buildings/{building_id}/shm", json={"stage": 3})
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                connection.execute("DELETE FROM buildings WHERE id = ?", (building_id,))
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM shm_demo WHERE building_id = ?", (building_id,)).fetchone()[0], 0)

    def test_pre_shm_database_gets_additive_table_without_reseeding_or_changing_records(self):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute("DROP TABLE shm_demo")
                connection.execute("UPDATE buildings SET name = 'Saved user edit' WHERE id = 1")
                connection.execute("UPDATE monthly_data SET electricity_kwh = 12345 WHERE building_id = 1 AND month = '2025-01'")
        baseline = self.client.get("/api/buildings/1").get_json()
        restarted = create_app(self.config).test_client()
        self.assertEqual(restarted.get("/api/buildings/1").get_json(), baseline)
        self.assertEqual(len(restarted.get("/api/buildings").get_json()["buildings"]), 4)
        self.assertEqual(restarted.get("/api/buildings/1/shm").get_json()["stage"], 0)

    def test_passport_exports_current_monitoring_stage_and_print_receives_it(self):
        saved = self.client.post("/api/buildings/1/shm", json={"stage": 3}).get_json()
        exported = self.client.get("/api/buildings/1/passport.json")
        self.assertEqual(exported.status_code, 200)
        self.assertEqual(exported.get_json()["structural_monitoring"], saved)
        with patch("app.render_template", return_value="Rendered test passport") as render:
            self.assertEqual(self.client.get("/passport/1?hvac=1").status_code, 200)
            self.assertEqual(render.call_args.kwargs["structural_monitoring"], saved)
            self.assertIsNotNone(render.call_args.kwargs["simulation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
