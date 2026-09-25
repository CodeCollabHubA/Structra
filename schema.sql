PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS buildings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    district TEXT NOT NULL DEFAULT '',
    building_type TEXT NOT NULL,
    year_built INTEGER NOT NULL CHECK (year_built BETWEEN 1950 AND 2100),
    floor_area_m2 REAL NOT NULL CHECK (floor_area_m2 > 0),
    occupants INTEGER NOT NULL CHECK (occupants > 0),
    floors INTEGER NOT NULL CHECK (floors > 0),
    description TEXT NOT NULL DEFAULT '',
    profile TEXT NOT NULL DEFAULT '',
    seed_profile TEXT NOT NULL DEFAULT 'typical',
    data_source TEXT NOT NULL DEFAULT 'Synthetic demo data — not a real building',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS monthly_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    month TEXT NOT NULL CHECK (month GLOB '2025-[01][0-9]'),
    electricity_kwh REAL NOT NULL CHECK (electricity_kwh >= 0),
    water_m3 REAL NOT NULL CHECK (water_m3 >= 0),
    waste_kg REAL NOT NULL CHECK (waste_kg >= 0),
    recycled_kg REAL NOT NULL CHECK (recycled_kg >= 0 AND recycled_kg <= waste_kg),
    maintenance_spend_aed REAL NOT NULL CHECK (maintenance_spend_aed >= 0),
    maintenance_completed INTEGER NOT NULL CHECK (maintenance_completed >= 0 AND maintenance_completed <= maintenance_due),
    maintenance_due INTEGER NOT NULL CHECK (maintenance_due >= 0),
    condition_score REAL NOT NULL CHECK (condition_score BETWEEN 0 AND 100),
    UNIQUE(building_id, month)
);

CREATE INDEX IF NOT EXISTS idx_monthly_data_building_month ON monthly_data(building_id, month);

-- Additive migration: existing buildings and utility records remain untouched.
-- A missing row means the baseline story stage, so reading the demo is read-only.
CREATE TABLE IF NOT EXISTS shm_demo (
    building_id INTEGER PRIMARY KEY REFERENCES buildings(id) ON DELETE CASCADE,
    stage INTEGER NOT NULL DEFAULT 0 CHECK (typeof(stage) = 'integer' AND stage BETWEEN 0 AND 3)
);
