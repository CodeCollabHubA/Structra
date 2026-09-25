# Structra — source handoff

**Team:** Qusai Aldaour and Ahmad Yasin

**Submission video:** https://youtu.be/r3bmYNfPFL8

**GitHub:** add the team's repository link when ready.

Structra's structural health monitoring (SHM) concept is the foundation. The Building Passport extends that concept with building operations, sustainability analysis, upgrade simulations and a shared printable record. The demo includes four fictional UAE buildings, monthly sample records and a scripted SHM inspection/maintenance story.

## Open and run

Work inside the repository root, which contains `app.py`. Python 3.10 or newer is required. Flask is the only direct dependency; SQLite is included with Python. There is no frontend build step or external API key.

Linux/macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Windows:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Open http://127.0.0.1:5000. Alternatively use `start-demo.bat` on Windows or `sh start-demo.sh` on Linux/macOS. The first install needs internet; the app then runs locally without external services.

The repository includes the original seed data at `sample_data.json`. On first launch it creates `instance/structra.db` locally; the database is ignored by Git. Saved changes persist in that database. Back it up before resetting it; see `README.md` for details.

## Validate

Linux/macOS: `.venv/bin/python -m unittest -v`

Windows: `.venv\Scripts\python.exe -m unittest -v`

The test suite covers the calculations, input validation, database persistence, exports, printable passport and SHM scenario. See `README.md` for the calculation assumptions and presenter script.

## Suggested continuation prompt for Devin

> Continue this existing Structra demo. Read README.md and run the test suite first. Keep Python Flask, SQLite and plain HTML/CSS/JavaScript; preserve the simple local setup. The app combines a scripted structural monitoring workflow with sustainability scores, deterministic recommendations, an upgrade simulator and a shared Building Passport. Preserve existing behavior and sample data while making requested improvements. Clearly identify fictional readings, projected savings and proposed municipal partnerships. Explain and test any changes you make.

## Demo and submission context

Use Creekside Business Centre for the main story: a simulated monitoring signal prompts a recorded demo inspection and maintenance follow-up, then operational upgrades improve the projected sustainability score from 57 to 73. Structural monitoring and sustainability share one building identity; the sustainability score does not certify structural safety.

The app was developed with Codex assistance. Runtime recommendations use deterministic rules, with no external AI model. This handoff enables future work in Devin; it does not claim that Devin was used for earlier development. Municipal collaboration in Abu Dhabi and Dubai remains a proposal.
