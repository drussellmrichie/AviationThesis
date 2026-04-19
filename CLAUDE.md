# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an aviation cognitive science honors thesis ("Clear Prop") at the University of Pennsylvania, combining Cognitive Science and Computer Science. The project builds and evaluates a computational cognitive model of aircraft landing automation, compared against empirical human pilot data, using the X-Plane flight simulator as the live testing environment.

## Running the Model

All active Python code lives in `Project_Code/Python3Model/src/`.

**Launch the experiment GUI (Streamlit app):**
```bash
cd Project_Code/Python3Model/src
python3 runThis.py
# Opens at http://localhost:8501
```

The GUI lets you configure experiment name, number, and an experiment setup CSV file, then starts/stops the model run in a background thread.

**Run an experiment directly (no GUI):**
```bash
cd Project_Code/Python3Model/src
python3 testPlatform.py
```

There is no build system, test suite, or linter configured. Dependencies are not pinned in a requirements file — key packages are `pyactr`, `streamlit`, `pandas`, `numpy`, `geographiclib`, and `matplotlib`.

## Architecture

### Execution Flow

```
runThis.py
  → gui.py (Streamlit web app)
    → testPlatform.runExperiment()  (experiment orchestrator)
      → cognitiveModel.AircraftLandingModel  (PI control logic + cognitive model)
        ↔ xpc/  (UDP socket to X-Plane simulator)
      → modelParameters.params()  (shared aircraft state + control values)
```

### Core Components

**`cognitiveModel.py`** — The cognitive/control model. `AircraftLandingModel` extends `pyactr.ACTRModel` and implements proportional-integral (PI) control laws for pitch, roll, yoke, rudder, and throttle. Contains bearing/radial-error calculations (via geographiclib), flare detection, and landing phase transitions. Writes control outputs back to X-Plane via DREFs.

**`modelParameters.py`** — Centralized state management. All aircraft state and control values flow through a single `params()` instance using a nested dictionary with 10 Enum classes (`listAccess`, `parameterType`, `visionModule`, `aircraftControls`, `flightPhase`, `integralValues`, `timeValues`, `permissions`). Access is permission-gated (READ/WRITE) — always use the provided accessor methods rather than direct dict access.

**`testPlatform.py`** — Experiment orchestrator. Loads weather/condition CSVs from `experiments/weather_files/`, sets initial simulator state via XPlaneConnect, runs the model loop, and logs results to CSV. Contains unit conversion helpers (feet↔meters, knots↔mph) and geodesic helpers (starting lat/long from distance/bearing, Euler-to-quaternion).

**`gui.py`** — Thin Streamlit wrapper. Runs `testPlatform` functions in background threads with a `threading.Event` for stop control.

**`xpc/`** — XPlaneConnect module. UDP socket communication with the X-Plane plugin: `getDREFs` reads simulator state, `sendDREF` writes values, `sendCTRL` sends flight control inputs.

### Experiment Setup Files

CSV files in `experiments/weather_files/` define test conditions (wind direction/speed, turbulence, thermal effects, cognitive delay). `testPlatform.runExperiment()` reads the active setup file row-by-row to drive each experimental trial.

### Data Pipeline

Experiment output CSVs are written to `Project_Data_Analysis/`. Analysis is done in Jupyter notebooks:
- `Project_Data_Analysis/Model_Data_Analysis/Data_Analysis_Pipeline.ipynb` — primary model analysis
- `Project_Data_Analysis/Empirical_Data_Analysis/` — human pilot comparison
- `Project_Data_Analysis/Combined_Data_Analysis/` — model vs. empirical comparison

Analysis focuses on descent rate, pitch/roll/altitude tracking, VCDI (Vertical Course Deviation Indicator) filtering for instrument approaches, and landing phase identification.

### Java Model

`Project_Code/JavaModel/` contains a legacy parallel implementation. `Model.java` manages a `MindQueue` of cognitive actions (VISION, MOTOR, DELAY). It is no longer the active implementation — the Python model is current.

## Environment Setup Notes

- **X-Plane has no headless mode.** It always requires a display and renders graphics. The best workaround is launching it normally, loading a flight, then minimizing — rendering overhead drops significantly when minimized. Do not launch it with `-WindowStyle Minimized` (causes crash on startup).
- **XPlaneConnect plugin** (v1.3-rc6) must be installed at `<X-Plane 12>/Resources/plugins/XPlaneConnect/`. It works with X-Plane 12 but may log deprecated DREF warnings — these are non-fatal.
- **Python interpreter**: always use `C:/Users/druss/miniconda3/python.exe`, not `python` or `python3` (the system stub redirects to the Microsoft Store).

## Key Conventions

- **Parameter access:** All reads/writes to aircraft state go through `modelParameters.params()` using the defined Enum keys. Do not add raw dict access.
- **Phase tracking:** Landing phases (descent, flare, rollout) are tracked via the `flightPhase` enum in `modelParameters`. Phase transitions live in `cognitiveModel.py`.
- **Control loop:** The PI integrator state is stored under `integralValues` in `modelParameters`; reset it when starting a new experiment run.
- **X-Plane DREFs:** All simulator variable names follow X-Plane DREF conventions (e.g., `sim/cockpit2/gauges/indicators/airspeed_kts_pilot`). The mapping between model parameters and DREFs is managed in `cognitiveModel.py`.
- **`Project_Data/` is gitignored** — raw simulation output is never committed.
