"""Load a scenario definition from a JSON file."""

import json
from pathlib import Path

from .models import Scenario, Station, Task


def load_scenario(path):
    """Read a scenario file and turn its values into Python data models."""
    scenario_path = Path(path)
    try:
        with scenario_path.open("r", encoding="utf-8") as file:
            raw = json.load(file)
    except FileNotFoundError as error:
        raise ValueError(f"Scenario file not found: {scenario_path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Scenario JSON is invalid: {error}") from error

    try:
        stations = [Station(**item) for item in raw["stations"]]
        tasks = [Task(**item) for item in raw["tasks"]]
        scenario = Scenario(
            name=raw["name"],
            time_steps=raw["time_steps"],
            stations=stations,
            tasks=tasks,
        )
    except (KeyError, TypeError) as error:
        raise ValueError(f"Scenario is missing a required field: {error}") from error

    validate_scenario(scenario)
    return scenario


def validate_scenario(scenario):
    """Reject values that would make the simulation invalid or misleading."""
    if scenario.time_steps < 1:
        raise ValueError("time_steps must be at least 1")
    if not scenario.stations:
        raise ValueError("The scenario must define at least one station")

    station_ids = [station.station_id for station in scenario.stations]
    task_ids = [task.task_id for task in scenario.tasks]
    if len(station_ids) != len(set(station_ids)):
        raise ValueError("Station IDs must be unique")
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("Task IDs must be unique")

    for station in scenario.stations:
        if station.compute_capacity <= 0 or station.energy_capacity <= 0:
            raise ValueError(f"{station.name}: capacities must be greater than zero")
        if not 0 <= station.energy_remaining <= station.energy_capacity:
            raise ValueError(f"{station.name}: starting energy must be within its capacity")
        if station.recharge_per_step < 0 or station.energy_per_compute < 0:
            raise ValueError(f"{station.name}: energy values cannot be negative")
        if station.bandwidth <= 0 or station.latency_steps < 0:
            raise ValueError(f"{station.name}: bandwidth must be positive and latency nonnegative")
        if any(step < 0 or step >= scenario.time_steps for step in station.outage_steps):
            raise ValueError(f"{station.name}: outage steps must be within the simulation")

    for task in scenario.tasks:
        if not task.task_type.strip():
            raise ValueError(f"{task.name}: task_type cannot be empty")
        if task.compute <= 0 or task.duration_steps < 1:
            raise ValueError(f"{task.name}: compute and duration must be greater than zero")
        if task.data_size < 0 or task.min_bandwidth < 0:
            raise ValueError(f"{task.name}: task resource values are invalid")
        if task.arrival_step < 0 or task.arrival_step >= scenario.time_steps:
            raise ValueError(f"{task.name}: arrival_step must be within the simulation")
