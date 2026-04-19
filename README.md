Clear Prop
# Introduction
This repository contains code for Chris Powell's Cognitive Science, Computer Science, Aviaition thesis project which began in August of 2024 as a senior honors thesis for the University of Pennsylvania's Cognitive Science program. 

# Setup & Installation

## Prerequisites

- Python (Miniconda/Anaconda recommended)
- Java JDK (for the legacy Java model only)
- [X-Plane 12](https://www.x-plane.com/desktop/try-it/) (demo is free, full version $59.99) — required for live simulation runs
- [XPlaneConnect plugin v1.3-rc6](https://github.com/nasa/XPlaneConnect/releases/tag/v1.3-rc6) installed into `<X-Plane 12>/Resources/plugins/XPlaneConnect/`

## Python Dependencies

```bash
pip install -r requirements.txt
```

Key packages: `streamlit`, `pyactr`, `geographiclib`, `rich`, `numpy`, `pandas`, `matplotlib`, `utm`, `colour`, `windrose`, `jupyterlab`

## Running the Model

All active Python code lives in `Project_Code/Python3Model/src/`. X-Plane must be running with an active flight loaded before starting the model.

**Launch the experiment GUI (Streamlit app):**
```bash
cd Project_Code/Python3Model/src
python runThis.py
# Opens at http://localhost:8501
```

**Run an experiment directly (no GUI):**
```bash
cd Project_Code/Python3Model/src
python testPlatform.py
```

## [Project Code](Project_Code)

### [Python3Model](Project_Code/Python3Model) — Active implementation

### [Java Model](Project_Code/JavaModel/) — Legacy, no longer active
