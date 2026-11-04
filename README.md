# ORBIT — Orbital Computing Resource Scheduler

ORBIT is a Python simulation for experimenting with how a network of orbital computing stations handles incoming work. The project is designed to grow from understandable scheduling rules into a richer simulation of energy, communication, priorities, station outages, and eventually an interactive control center.

> **Current status:** ORBIT now has a runnable multi-step command-line simulation. It reads a scenario from JSON, prioritizes tasks, checks station compute/energy/bandwidth limits, models scheduled station outages, and compares First Fit, Best Fit, and Energy Aware scheduling. The model uses simplified abstract units and is an educational simulator, not a physical satellite model.

## What it can do now

- Load stations, tasks, and simulation length from `scenarios/default.json`.
- Add new tasks at different simulation steps and sort waiting work by priority.
- Respect each station's compute capacity for each step, energy budget, and bandwidth requirement.
- Recharge station energy between steps, up to the station's energy capacity.
- Take stations offline at configured simulation steps.
- Estimate communication delay from station latency and task data size / station bandwidth.
- Compare three scheduling rules against the same scenario.
- Report assigned and unassigned tasks, energy use, outage steps, and estimated communication delay.

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

## Project structure

```text
orbit-project/
├── README.md                  # Project guide, status, and design notes
├── orbit_day1.py              # Standalone beginner First Fit / Best Fit example
├── orbit/                     # Implemented simulator package
│   ├── __init__.py            # Package version
│   ├── __main__.py            # Command-line entry point (`python -m orbit`)
│   ├── algorithms.py          # First Fit, Best Fit, and Energy Aware choices
│   ├── models.py              # Task, Station, Scenario, Assignment, RunResult
│   ├── scenario.py            # JSON loading and input validation
│   ├── simulation.py          # Time steps, arrivals, resources, outages, assignments
│   └── report.py              # Comparison table and detailed run reports
├── scenarios/
│   └── default.json           # Demonstration network and task workload
├── tests/                     # Planned: automated behavior checks
├── results/                   # Planned: saved experiment reports
└── dashboard/                 # Planned: interactive visual control center
```

## How the simulation works

1. **Load the scenario.** `scenario.py` reads the JSON file and creates `Station` and `Task` objects.
2. **Start a simulation run.** The command-line entry point calls `run_simulation` once per selected algorithm. Each run gets its own copy of the input, so strategies start with identical station resources.
3. **Advance through time steps.** At each step, newly arrived tasks join the waiting list. Tasks with a larger priority number are considered first.
4. **Update station resources.** A station is marked offline if the current step is in its outage list. Online stations recharge energy and receive a fresh compute budget for the step.
5. **Find eligible stations.** A task can be assigned only when a station is online, has enough compute and energy, and meets the task's minimum bandwidth.
6. **Apply the scheduling rule.** The chosen algorithm selects one eligible station. The simulation subtracts the task's compute and energy costs and records the assignment.
7. **Try waiting tasks again.** Tasks that could not fit remain in the queue for the next step. Any still waiting after the final step are reported as unscheduled.
8. **Report results.** `report.py` prints an algorithm comparison and details for each run.

## Data models

The models in `orbit/models.py` use Python `dataclass` declarations. A dataclass groups named values into one readable object.

### Task

Each task has an ID, name, compute demand, priority, arrival step, data size, and minimum bandwidth. Larger priority values are scheduled first. Compute is charged against a station's per-step capacity and energy use.

### Station

Each station has an ID, name, per-step compute capacity, battery capacity and starting energy, energy recharge rate, energy cost per compute unit, bandwidth, communication latency, and a list of outage steps.

### Assignment

An assignment records the task and station, the step at which it was scheduled, an estimated completion step, energy spent, and estimated communication delay.

### RunResult

A run result collects assignments, tasks that remained unscheduled, total energy used by station, and the number of outage steps each station experienced. The report uses these values to compare algorithms.

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
  "name": "Emergency weather scan",
  "compute": 5,
  "priority": 5,
  "arrival_step": 0,
  "data_size": 6,
  "min_bandwidth": 3
}
```

All values are intentionally small and abstract. `arrival_step` and each outage step must be within the configured simulation horizon. Station and task IDs should be unique. The loader checks core inputs and prints a useful error when the scenario is malformed.

## Model assumptions and current limits

The current version is a foundation for experiments, so its simplifications should be understood when presenting it:

- Compute and energy are abstract values chosen for the scenario, not measured hardware units.
- A task consumes its compute budget in one scheduling step. Task execution over multiple steps is not modeled yet.
- Communication delay is estimated as station latency plus `ceil(data_size / bandwidth)`. It affects the estimated completion step, but does not reserve station resources while data is in transit.
- An outage makes a station unavailable for assignment at the listed step. Recovery is automatic on later steps; running-task recovery is not modeled.
- There is no orbital mechanics, real network topology, randomness, data persistence, or graphical dashboard yet.

These limits make the scheduling decisions visible and easier to explain while leaving a clear path to a more realistic model.

## Testing plan

Automated tests are planned but are not included yet. Useful first cases include exact-capacity assignments, insufficient energy, minimum-bandwidth rejection, task priority ordering, delayed arrivals, outage handling, and a task that remains unscheduled after the horizon. The demo scenario can also be run with each scheduler to compare behavior.

## Development roadmap

1. **Current foundation:** structured package, configurable scenario, time-step arrivals, priority ordering, compute/energy/bandwidth checks, outages, delay estimates, three scheduler choices, and reports.
2. **Validation and tests:** add focused automated checks for resource limits and simulation lifecycle.
3. **Task execution lifecycle:** track queued, transferring, running, completed, failed, and expired task states across steps.
4. **Network model:** introduce links between stations, transfer contention, and route-dependent delays.
5. **Failure and recovery behavior:** model task interruption, retry, reassignment, and recovery events.
6. **Experiment outputs:** save results as CSV/JSON and compare algorithms across repeatable scenarios.
7. **Visual control center:** add charts and controls after the simulator behavior and outputs are stable.

## Presentation summary

“ORBIT is a Python simulator for scheduling computing tasks across resource-limited orbital stations. Tasks arrive over time and carry a priority, compute demand, and communication requirement. Each station has compute, energy, bandwidth, and outage limits. I implemented three scheduling rules and compare their assignment, energy, and delay results using the same scenario. The current model is simplified: each task uses compute in one scheduling step, and communication delay is an estimate. The next step is tracking task execution and recovery across multiple steps.”
