# Structra — Structural Monitoring + Building Passport

**Better buildings. Stronger cities.**

A complete local hackathon demo connecting Structra's structural health monitoring (SHM) story with a sustainability passport: monitor a building, record a review and maintenance response, explore operational improvements, and share one building record.

**All buildings, readings, inspection events, costs, emissions and projections in this project are fictional demo data.** The examples are inspired by common UAE building types; they do not describe named real properties. Structra's sustainability score is a transparent demonstration model, not an official building rating, structural safety assessment or certification. The SHM sequence uses scripted signals and reports, with no live sensors or actual engineer review.

## Run the demo

You need **Python 3.10 or newer**. Flask is the only direct package dependency. SQLite ships with Python. Internet access is needed for the first package installation; the working demo needs no external APIs, accounts or internet connection.

Open a terminal **inside the repository root**, the folder containing `app.py`.

### Windows (PowerShell or Command Prompt)

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

If your installation uses `python` instead of the Windows `py` launcher, use `python -m venv .venv` for the first command. No PowerShell activation-policy changes are necessary.

Or double-click **`start-demo.bat`**. It creates the local environment and installs Flask if needed. The launcher looks for `py`, then `python`, and automatically falls back to Codex's bundled Python at `%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` when neither command is available. Once the local environment contains Flask, subsequent launches work offline.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Or run **`sh start-demo.sh`** from the project folder. On Linux, your Python installation must include the `venv` module.

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)**. Keep the terminal open while presenting. Press **Ctrl+C** in the terminal to stop the server. Restarting the app preserves your saved edits.

If port 5000 is already in use, stop the other local app using that port and run Structra again, or set the `PORT` environment variable to another port. For example, in PowerShell run `$env:PORT="5001"` before starting and open `http://127.0.0.1:5001`. In macOS/Linux run `PORT=5001 .venv/bin/python app.py`. Use a current desktop browser; no build step or JavaScript package manager is required.

## What works

- A portfolio dashboard with four distinct sample buildings and monthly performance charts.
- Building selection and a form to add your own fictional demo building.
- Twelve months of electricity, water, waste, recycling and maintenance records per seeded building.
- Editable monthly records saved in SQLite, with input validation and recalculated scores.
- A **Structural monitoring** view combining fictional crack, vibration and tilt readings with a scripted inspection and maintenance history.
- A repeatable SHM scenario saved separately for each building: baseline, signal change, demo inspection, then demo maintenance.
- A transparent sustainability score and deterministic, data-driven recommendations.
- A what-if simulator for HVAC optimization, LED lighting, solar panels, leak repair and preventive maintenance.
- Baseline-versus-projected scores, resource use, operating cost and electricity emissions.
- A shared digital Building Passport connecting the SHM history with operational performance, a print-friendly report, and downloadable data exports.
- A **Municipal pilot** concept focused on Abu Dhabi and Dubai, with proposed collaboration clearly identified.

## Simple architecture

```text
Browser: HTML + CSS + plain JavaScript
                   |
             Flask / Python
                   |
               SQLite
```

The browser requests data from the local Flask server. Python calculates scores and recommendations using fixed rules; no AI model or external service is called. The simulator recalculates a copy of the saved data, so experimenting does not overwrite the baseline.

The SHM workflow is a demonstration extension of Structra's original monitoring concept. This project does not connect to an existing production Structra installation or sensor platform. Both parts share the same building identity in this local app, while their calculations remain distinct: completing a scripted inspection does not improve the sustainability score or certify structural safety.

## Show evidence for the judging themes

| Theme | What to demonstrate |
| --- | --- |
| Innovation | One building identity connects monitoring signals, review history, maintenance and resource decisions. Show the path from a signal change to an action record, then to an operational improvement plan and shared passport. |
| Demo quality | Run the three SHM steps, refresh to demonstrate saved state, then toggle upgrades and open the projected print report. Clearly identify simulated readings and projected results. |
| Practicality | Four building types, editable records, local SQLite storage, explainable calculations and CSV/JSON/PDF-via-print outputs. A first pilot could start with existing inspection reports, utility bills and maintenance records. |
| AI-assisted development | Show the working source and automated checks as evidence of an AI-assisted build. Explain the development process separately from the app's runtime calculation method. |

**Development provenance:** the original demo was built with Codex-assisted coding and testing, and the source was subsequently migrated into this repository with Devin assistance. Its running recommendation engine uses deterministic rules and does not call a runtime AI model.

## Proposed municipal pilot

The **Municipal pilot** area presents a concept for **Abu Dhabi and Dubai, with partnership and patronage pending confirmation**. No municipality, official sponsor, endorsement or government integration is confirmed by this project, and no official logo is supplied.

A practical next step would be to invite building owners, verify their bills, floor areas and inspection records, agree locally appropriate benchmarks with the participating authority, and measure outcomes after selected improvements. The useful pilot measures are data completeness, buildings onboarded, inspection follow-up, actions adopted, and measured changes in resource use. The current demo supplies the owner workflow and illustrative scenarios; a municipal agreement, qualified engineering oversight and verified measurements would establish the next stage.

Official references provide local context:

- **Dubai:** Dubai Municipality describes the city's green-building rating framework in [Al Sa'fat — Dubai Green Building System](https://www.dm.gov.ae/municipality-business/al-safat-dubai-green-building-system/).
- **Abu Dhabi:** Abu Dhabi City Municipality describes the Estidama Pearl Rating System in its [sustainable green building overview, 8 January 2025](https://www.dmt.gov.ae/en/adm/Media-Centre/News/08Jan2025).

Structra's score, thresholds and simulations are independent demo assumptions. These references do not establish Al Sa'fat or Estidama compliance, certification, affiliation or approval for Structra.

## Data and persistence

The app seeds its SQLite database on first launch. The live database is **`instance/structra.db`**, generated locally and excluded from Git, while **`sample_data.json`** is the readable starting dataset. Once the database exists, changing the JSON does not overwrite saved records.

The four fictional examples each contain twelve monthly records from **January to December 2025**, with stronger cooling demand in summer:

| Fictional building | Type / city | Operating story | Area (m²) | Annual grid electricity (kWh) | Annual water (m³) |
| --- | --- | --- | ---: | ---: | ---: |
| Creekside Business Centre | Office / Dubai | Older office with high cooling demand and a maintenance backlog | 18,000 | 4,410,000 | 10,800 |
| Al Noor Residences | Residential / Sharjah | Balanced residential operations with improvement potential | 24,500 | 3,552,501 | 36,750 |
| Oasis Retail Pavilion | Retail / Abu Dhabi | Strong operations and waste separation | 8,200 | 1,312,001 | 3,935.9 |
| Horizon Mixed-use Hub | Mixed-use / Dubai | Water consumption and waste diversion need attention | 31,000 | 5,735,000 | 49,599.9 |

Monthly records track grid electricity (kWh), water (m³), total and recycled waste (kg), maintenance expenditure (AED), tasks due/completed, and a recorded condition score out of 100. Maintenance expenditure is displayed as operational context; it is not included in utility savings or used as a proxy for health.

Use the monthly data editor to change readings and save them. Reloading the page or restarting the app keeps these changes. New buildings start with a generated synthetic annual profile so they can immediately be explored in the demo.

Each building also has its own saved SHM scenario stage. Switching buildings does not advance another building's scenario, and refreshing or restarting preserves the selected stage. **Reset SHM scenario** resets that building's monitoring story without changing its monthly utility data.

For new buildings, choose a typical, efficient or needs-attention profile. The generator scales a same-type sample: electricity and maintenance expenditure follow floor area; water and waste follow occupants. It then applies profile adjustments and preserves the monthly seasonal pattern. These generated readings are editable.

**Exports:** `Export monthly CSV` downloads the twelve saved operational rows. The passport JSON contains the baseline profile, records, analysis, SHM state and demo provenance. `Print passport` opens the baseline print view; `Print projected passport` in **Upgrade simulator** includes the selected operational scenario and its assumptions. Both printable pages include the current SHM summary and event history. Use the browser's print dialog to save a PDF. An operational upgrade scenario is included in the print-page URL, so reopening that URL recalculates it from the current saved baseline; these upgrade scenarios are not database records. The SHM stage is saved in SQLite.

To start fresh, stop the app, rename `instance/structra.db` to a backup filename, then restart the app. It recreates the original sample database. Keep the backup if you want to restore your saved edits later.

## How the score works

The implementation lives in `scoring.py`. Each component is bounded from 0 to 100. The overall score uses **35% energy + 25% water + 20% waste + 20% Asset care (maintenance performance)**, calculated from unrounded component scores and rounded once for display. The internal `health` field supplies **Asset care**; it is not a structural certification or SHM safety score.

Energy measures purchased grid electricity per square metre per year. Water measures cubic metres per square metre per year. Both use a linear scale:

```text
component score = 100 × (poor threshold − measured intensity)
                        / (poor threshold − good threshold)
```

Values at or below the good threshold score 100; values at or above the poor threshold score 0. The thresholds are invented, building-type-specific demo settings:

| Building type | Energy: good / poor (grid kWh/m²/year) | Water: good / poor (m³/m²/year) |
| --- | ---: | ---: |
| Office | 110 / 360 | 0.25 / 1.10 |
| Residential | 90 / 260 | 0.80 / 2.80 |
| Retail | 140 / 440 | 0.35 / 1.30 |
| Mixed-use | 115 / 330 | 0.60 / 2.00 |

- **Waste:** recorded recycled share ÷ 70% × 100, capped at 100. Zero recorded waste produces a zero waste score because diversion performance is unknown.
- **Asset care (maintenance performance):** 65% of the average recorded condition score plus 35% of the percentage of scheduled maintenance tasks completed. If no tasks are due, completion is treated as 100%. These operational records do not establish the structural condition of a building.
- **Demo rating:** A ≥ 85, B ≥ 70, C ≥ 55, D ≥ 40, E below 40.
- **Partial records:** intensity is annualized by `12 / number of recorded months`; period totals remain the actual recorded totals. This simple annualization does not correct for seasonality. The analysis flags incomplete annual data; the standard demo always starts with twelve months.

The score is sensitive to floor area and reported readings. A higher score indicates stronger performance **within this demo model**; it is not a safety assessment or an official UAE sustainability standard.

## Structural monitoring scenario

Open **Structural monitoring** after selecting a building. The workflow has four stages:

| Stage / control | What the demo shows |
| --- | --- |
| Baseline / **Reset SHM scenario** | The initial fictional crack, vibration and tilt readings, ready to repeat the story. |
| **Simulate a signal change** | A scripted change that would prompt review in the proposed workflow. It is not an automated diagnosis. |
| **Record demo inspection** | A fictional inspection entry demonstrating how a qualified person's review could be recorded. No actual engineer has reviewed the readings. |
| **Record demo maintenance** | A scripted maintenance response and follow-up record, retained in the building's SHM history. |

The sequence demonstrates **monitor → review → maintain**. It does not infer structural safety from a crack width, vibration value or tilt reading. Real monitoring needs sensor context, calibration, site-specific limits and qualified interpretation. The local-repair narrative is an invented case to show how a documented maintenance decision could help care for existing assets; it is not a repair recommendation for a real building.

Each stage presents a predefined signal trace and event history. The final follow-up does not reset all readings to the original values or prove repair effectiveness: continued observation remains part of the story. SQLite stores the current stage for each building; this is a repeatable scenario rather than a live telemetry or engineering records system.

The sustainability link is the shared decision record: owners can maintain existing assets while also reducing operational resource use. The demo does not quantify avoided material carbon or extra service life. Only the separate upgrade simulator changes the projected resource metrics and sustainability score; SHM stage changes do not alter those calculations.

## The combined demo story

**Creekside's summer wake-up call.** Sara manages the fictional Creekside Business Centre, an 18,000 m² office building in Dubai. She is responsible for both the building's upkeep and its operating bills, but monitoring reports, maintenance notes and monthly consumption usually sit in separate places.

She starts with Structra's original SHM purpose: spotting a signal change and keeping a record of the response. In the scripted demonstration, she sees a changing crack signal alongside vibration and tilt readings, records a fictional inspection, and records the example's local maintenance response. The history stays with the building, so a future reviewer can follow what was observed and what was recorded in response.

Then she opens the operational view. Creekside's original sample sustainability score is **57/100**, with high electricity use and opportunities to improve water use and maintenance completion. She tests HVAC optimization, LEDs, solar, water leak repair and preventive maintenance. Under the stated demo assumptions, the projected score becomes **73/100**, purchased electricity falls by approximately **31%**, and water use falls by **18%**. These projections are independent of the SHM steps; they are not measured outcomes.

Sara generates one Building Passport with the SHM history, operational baseline and proposed upgrade plan. In a future Dubai or Abu Dhabi pilot, participating owners could share that common record for agreed review and follow-up. Municipal collaboration and patronage remain proposed.

**Pitch line:** “Structra connects how a building is monitored, how it is maintained and how efficiently it operates—one history, one improvement plan, one Building Passport.”

## Simulator assumptions

The simulator changes a copy of the current building's monthly records, recalculates the same score, and compares the result with the saved baseline. Switching all controls off returns to baseline.

| Intervention | Illustrative model |
| --- | --- |
| HVAC optimization | Reduce electricity demand by 12%. |
| LED upgrade | Reduce the electricity demand remaining after HVAC optimization by 8%. |
| Solar panels | Offset 15% of grid electricity remaining after demand savings. Physical electricity demand is unchanged by solar. |
| Water leak repair | Reduce water consumption by 18%; this is a scenario, not a diagnosis that a leak exists. |
| Preventive maintenance | Complete half of each month's outstanding tasks, rounded up, and add up to 8 condition points, capped at 100. |

For example, combining HVAC, LEDs and solar leaves `0.88 × 0.92 × 0.85 = 68.816%` of baseline purchased electricity: a **31.184% reduction**, rather than adding the three savings percentages. Waste does not change in these five scenarios. Preventive maintenance is not assigned an energy, carbon or monetary saving.

Utility costs use **AED 0.38/kWh** and **AED 8/m³**. Electricity emissions use **0.40 kg CO₂e per grid kWh**. These are deliberately simple invented demo factors, not current tariffs or verified emissions factors. Savings cover the displayed data period and are annual only for a complete twelve-month calendar year. Capital costs, payback and solar installation feasibility are outside this demo.

Recommendation order follows deterministic priorities based on component scores: below 55 is high priority, below 80 is medium, and 80 or above is low. Solar is always offered as a medium-priority exploration. The waste recommendation is informative; it does not have a simulator control.

## Present it in 2–3 minutes

**0:00–0:20 — One owner, two connected needs.** Open **Overview** with **Creekside Business Centre** selected. “Sara manages this fictional Dubai office building. She needs to keep its maintenance history in order and reduce high summer resource use. Structra brings both into the same building record.”

**0:20–0:45 — Start with original Structra SHM.** Open **Structural monitoring**, then click **Simulate a signal change**. Point to the crack, vibration and tilt readings. “Our original monitoring story starts here: a signal changes and needs review. These readings are scripted for the demo; the app is not diagnosing a defect.”

**0:45–1:15 — Show the human review and response.** Click **Record demo inspection**, explain the fictional report, then click **Record demo maintenance**. Point to the history. “We keep the observation, review and maintenance response together. In this example, the recorded response is local maintenance. A real case would need qualified engineering judgment.” Refresh once to show the saved state if time allows.

**1:15–1:55 — Add the sustainability decision.** Open **Upgrade simulator** and click **Apply demo improvement plan**. Show the baseline and projected scores, purchased electricity and water use; toggle one action off and back on. “The same owner can test operational improvements before committing money. These assumptions project the score from **57 to 73**, with about **31% less purchased electricity** and **18% less water**. The SHM history remains separate from this calculation.” Use the actual figures shown if sample records have been edited.

**1:55–2:20 — Share the combined passport.** From **Upgrade simulator**, click **Print projected passport** to show the report and its SHM history. “One passport now connects the monitoring and maintenance history with the operational baseline and proposed upgrades. It shows what was recorded and what is only projected.” Return to the app and open **Building Passport** to show the saved baseline identity; its **Print passport** option also includes the SHM summary and history.

**2:20–2:50 — Connect the pilot and the build.** Open **Municipal pilot**. “We propose a Dubai or Abu Dhabi pilot to verify records, agree review processes and measure outcomes. Partnership and patronage are pending. This working prototype was built with Codex-assisted coding; its runtime uses transparent rules.” Close with: “Monitor, review, maintain, optimize—one Structra Building Passport.”

**Before presenting:** select Creekside, click **Reset SHM scenario**, clear any selected upgrade controls, and rehearse the click path. The **57 → 73** figures assume the untouched sample records; use the actual on-screen figures after any edits. For follow-up questions, show **Building data**, save a changed monthly reading and refresh to demonstrate persistence; also show **Add building**, the methodology, exports or automated checks. Identify Codex as the original development assistant, Devin as the repository migration assistant and deterministic rules as the runtime method. Do not claim live sensors, engineering approval or a confirmed municipal partnership.

## Project files and checks

| File / folder | Purpose |
| --- | --- |
| `app.py` | Flask routes, validation, data persistence and exports |
| `scoring.py` | Score methodology, rules and reversible simulator |
| `shm.py` | Fictional SHM signals, scripted scenario stages and event history |
| `schema.sql` | SQLite tables and constraints |
| `sample_data.json` | Four fictional buildings and 48 monthly records |
| `templates/` | Main app and printable passport pages |
| `static/` | Local stylesheet and browser JavaScript |
| `instance/structra.db` | Live SQLite database, created on first run |
| `test_app.py` | Automated behavior checks using disposable databases |
| `test_shm.py` | SHM scenario behavior and integration checks |
| `start-demo.bat` / `start-demo.sh` | Optional local setup and launch shortcuts |

Run the automated checks from the project folder:

```powershell
# Windows
.venv\Scripts\python.exe -m unittest -v
```

```bash
# macOS / Linux
.venv/bin/python -m unittest -v
```

Checks cover initial seeding, deterministic scores, simulator savings and baseline preservation, input validation, add/edit persistence after restart, SHM stage transitions and persistence, exports and rendered print views. They create temporary databases and do not change your saved demo data. For a quick visual check, select each building, run and reset the SHM scenario, edit and save a month, switch simulator controls, and open the baseline and projected print pages.

## Demo scope

This is a local, single-user prototype extending the Structra SHM concept with a sustainability workflow, not an integration with an existing production system. Utility readings are entered or generated rather than extracted from bills. SHM readings, inspection reports and maintenance events are fictional, scripted examples. Recommendations are reproducible rules rather than generative AI. Scenario results are annual estimates under stated demo assumptions; they are not engineering assessments, contractor quotes or verified savings. Electricity emissions cover purchased electricity only, and the score does not represent a whole-life carbon assessment or structural safety.

No logins, cloud database, payments, live sensors or external API keys are needed. Stop the local server after your demo. A production version would need verified source data, sensor integration and calibration where applicable, qualified engineering review, locally appropriate benchmarks, authentication and deployment work.
