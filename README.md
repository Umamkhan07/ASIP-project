# ORBIT — Orbital Computing Resource Scheduler

ORBIT is a Python simulation for experimenting with how a network of orbital computing stations handles incoming work. It includes a terminal simulator and a browser-based control room for watching tasks move through simulation steps.

> **Current status:** ORBIT has a multi-step command-line simulator and a local browser dashboard. Tasks now have explicit types and different compute demands, data sizes, priorities, and run durations. Work can continue across steps, pause during outages or resource shortages, and complete later. Values remain simplified educational units, not a physical satellite model.

## What it can do now

- Load stations, tasks, and simulation length from `scenarios/default.json`.
- Represent workload types such as image generation, image analysis, weather lookup, navigation, and telemetry.
- Give each task a compute demand per work step and a duration in work steps.
- Add new tasks at different simulation steps and sort waiting work by priority.
- Respect each station's compute capacity for each step, energy budget, and bandwidth requirement.
- Recharge station energy between steps, up to the station's energy capacity.
- Take stations offline at configured simulation steps.
- Continue running tasks over multiple steps and pause them when a station is offline or lacks resources.
- Estimate communication delay from station latency and task data size / station bandwidth.
- Compare three scheduling rules against the same scenario.
- Report assigned and unassigned tasks, energy use, outage steps, and estimated communication delay.
- Show a visual orbital network with station resource meters, step events, and playback controls.

The original small `orbit_day1.py` exercise remains available as a standalone introduction to First Fit and Best Fit. The package version is the main project from this point forward.

## Run it

You need Python 3.10 or newer. The simulator uses only Python's standard library, so no packages need to be installed.

1. Open this project folder in VS Code.
2. Choose **Terminal → New Terminal**.
3. Run the comparison:

   ```powershell
   python -m orbit
   ```

   On Windows, `py -m orbit` may work if `python` is not recognized.

The default command compares all three algorithms. To run one algorithm at a time:

```powershell
python -m orbit --algorithm first_fit
python -m orbit --algorithm best_fit
python -m orbit --algorithm energy_aware
```

To use another scenario JSON file:

```powershell
python -m orbit --scenario scenarios/default.json --algorithm compare
```

There are no third-party dependencies. Run commands from the project root (the folder containing `README.md` and the `orbit` folder).

To open the visual control room, run:

```powershell
python -m orbit --dashboard
```

ORBIT starts a local-only web server and opens the dashboard in your browser. Keep the terminal open while using it; press **Ctrl+C** there to stop the server. Use the scheduler menu to switch algorithms and the playback controls to move through the time steps. If port 8000 is already in use, try `python -m orbit --dashboard --port 8001`.

## Project structure

```text
orbit-project/
├── README.md                  # Project guide, status, and design notes
├── orbit_day1.py              # Standalone beginner First Fit / Best Fit example
├── orbit/                     # Implemented simulator package
│   ├── __init__.py            # Package version
│   ├── __main__.py            # Command-line entry point (`python -m orbit`)
│   ├── dashboard.py           # Local web server and simulation data endpoint
│   ├── algorithms.py          # First Fit, Best Fit, and Energy Aware choices
│   ├── models.py              # Tasks, stations, task progress, assignments, step snapshots
│   ├── scenario.py            # JSON loading and input validation
│   ├── simulation.py          # Task lifecycle, resource use, outages, assignments
│   ├── report.py              # Comparison table and detailed run reports
│   └── dashboard/
│       └── index.html         # Browser control room
├── scenarios/
│   └── default.json           # Demonstration network and task workload
├── results/                   # Planned: saved experiment reports
└── tests/                     # Planned: automated behavior checks
```

## How the simulation works

1. **Load the scenario.** `scenario.py` reads the JSON file and creates `Station` and `Task` objects.
2. **Start a simulation run.** The command-line entry point calls `run_simulation` once per selected algorithm. Each run gets its own copy of the input, so strategies start with identical station resources.
3. **Advance through time steps.** At each step, newly arrived tasks join the waiting list. Tasks with a larger priority number are considered first.
4. **Update station resources.** A station is marked offline if the current step is in its outage list. Online stations recharge energy and receive a fresh compute budget for the step.
5. **Continue existing work.** Running tasks use compute and energy for one work step. Tasks pause if their station is offline or cannot supply the needed resources; they resume when resources are available.
6. **Find eligible stations for waiting tasks.** A task can be assigned only when a station has enough remaining compute and energy for one work step, and meets the task's minimum bandwidth.
7. **Apply the scheduling rule.** The chosen algorithm selects one eligible station. The simulation subtracts one work step of compute and energy and records the assignment.
8. **Try waiting tasks again.** Tasks that could not fit remain in the queue. Tasks are reported as completed, in progress, paused, or unscheduled when the run ends.
9. **Present results.** `report.py` prints a comparison in the terminal. The browser dashboard uses the same step snapshots to show task progress.

## Data models

The models in `orbit/models.py` use Python `dataclass` declarations. A dataclass groups named values into one readable object.

### Task

Each task has an ID, name, task type, compute demand per work step, duration in work steps, priority, arrival step, data size, and minimum bandwidth. Larger priority values are scheduled first. A compute-heavy task needs a station with more capacity; a long task uses compute and energy across more steps. A data-heavy task affects the communication-delay estimate.

### Station

Each station has an ID, name, per-step compute capacity, battery capacity and starting energy, energy recharge rate, energy cost per compute unit, bandwidth, communication latency, and a list of outage steps.

### Assignment

An assignment records the task and station, the step at which it was scheduled, an estimated completion step, energy spent, and estimated communication delay.

### RunResult

A run result collects assignments, each task's final state, tasks that remained unscheduled, total energy used by station, and the number of outage steps each station experienced. The report uses these values to compare algorithms.

It also contains a `StepSnapshot` for each simulation step. Each snapshot records station availability and resources, assignments, new arrivals, and waiting tasks. The dashboard uses these snapshots for playback.

## Scheduling strategies

All scheduler classes follow the same small interface: `choose_station(task, candidates)` receives a task and the stations that satisfy the resource checks, then returns one station or `None`.

- **First Fit:** picks the first eligible station in the scenario file's order.
- **Best Fit:** picks the eligible station with the least compute capacity left in the current step after taking the task.
- **Energy Aware:** picks the eligible station that retains the largest share of its battery after taking the task.

The scheduler chooses a station; `simulation.py` checks eligibility and applies the resource changes. This keeps algorithm decisions separate from simulation bookkeeping.

## Scenario configuration

Edit `scenarios/default.json` to change the sample system. A station entry looks like this:

```json
{
  "station_id": "AURORA",
  "name": "Aurora Station",
  "compute_capacity": 8,
  "energy_capacity": 24,
  "energy_remaining": 20,
  "recharge_per_step": 3,
  "energy_per_compute": 0.8,
  "bandwidth": 8,
  "latency_steps": 1,
  "outage_steps": []
}
```

A task entry looks like this:

```json
{
  "task_id": "T-01",
  "name": "Weather record lookup",
  "task_type": "weather_lookup",
  "compute": 1,
  "duration_steps": 1,
  "priority": 1,
  "arrival_step": 0,
  "data_size": 6,
  "min_bandwidth": 3
}
```

All values are intentionally small and abstract. `arrival_step` and each outage step must be within the configured simulation horizon. Station and task IDs should be unique. The loader checks core inputs and prints a useful error when the scenario is malformed.

## Model assumptions and current limits

The current version is a foundation for experiments, so its simplifications should be understood when presenting it:

- Compute and energy are abstract values chosen for the scenario, not measured hardware units.
- `compute` is the capacity needed for each work step; `duration_steps` says how many successful work steps the task needs. The model does not simulate partial work within a step.
- Communication delay is estimated as station latency plus `ceil(data_size / bandwidth)`. It affects the estimated completion time, but is not yet a real transfer phase and does not delay task execution.
- An outage pauses running work at that station. Work resumes automatically when the station returns; retrying elsewhere or permanent failures are not modeled.
- There is no orbital mechanics, real network topology, or data persistence. The dashboard visualizes the same simplified model used by the terminal simulator.

These limits make the scheduling decisions visible and easier to explain while leaving a clear path to a more realistic model.

## Testing plan

Automated tests are planned but are not included yet. Useful first cases include exact-capacity assignments, insufficient energy, minimum-bandwidth rejection, task priority ordering, delayed arrivals, outage handling, and a task that remains unscheduled after the horizon. The demo scenario can also be run with each scheduler to compare behavior.

## Development roadmap

1. **Current foundation:** configurable typed workloads, multi-step task execution, resource checks, outages and pauses, three schedulers, terminal reports, and dashboard playback.
2. **Validation and tests:** add focused automated checks for resource limits and task progress.
3. **Network model:** make data transfers take time and compete for link bandwidth.
4. **Failure and recovery behavior:** add failure durations, retry, reassignment, and recovery events.
5. **More scheduling rules:** add Round Robin, Least Loaded, and deadline-aware strategies.
6. **Experiment outputs:** save results as CSV/JSON and compare algorithms across repeatable scenarios.
7. **Expand the control room:** add scenario editing and side-by-side algorithm charts.

## Presentation summary

“ORBIT is a Python simulator for scheduling different kinds of computing tasks across resource-limited orbital stations. Each task has its own compute demand and run duration, while stations have compute, energy, bandwidth, and outage limits. I compare three scheduling rules and visualize tasks as they wait, run, pause, and complete. Communication delay is still estimated; the next step is modeling real data transfers between stations.”
