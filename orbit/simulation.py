"""Run the discrete time-step simulation."""

from copy import deepcopy
from math import ceil

from .models import Assignment, RunResult


def run_simulation(scenario, scheduler_class):
    """Schedule arriving tasks while checking station resources and outages."""
    stations = deepcopy(scenario.stations)
    tasks = deepcopy(scenario.tasks)
    scheduler = scheduler_class()

    tasks_by_arrival = {}
    for task in tasks:
        tasks_by_arrival.setdefault(task.arrival_step, []).append(task)

    pending = []
    assignments = []
    last_reason = {}
    energy_used_by_station = {station.station_id: 0.0 for station in stations}
    offline_steps_by_station = {station.station_id: 0 for station in stations}

    for step in range(scenario.time_steps):
        pending.extend(tasks_by_arrival.get(step, []))

        for station in stations:
            station.step_compute_left = station.compute_capacity
            station.offline = step in station.outage_steps
            if station.offline:
                offline_steps_by_station[station.station_id] += 1
            else:
                station.energy_remaining = min(
                    station.energy_capacity,
                    station.energy_remaining + station.recharge_per_step,
                )

        # Higher-priority work is offered to schedulers first.
        pending.sort(key=lambda task: task.priority, reverse=True)
        still_waiting = []

        for task in pending:
            candidates = []
            reasons = []

            for station in stations:
                if station.offline:
                    reasons.append("all possible stations are offline")
                    continue
                if station.step_compute_left < task.compute:
                    reasons.append("not enough compute capacity this step")
                    continue
                if station.bandwidth < task.min_bandwidth:
                    reasons.append("station bandwidth is too low")
                    continue

                energy_cost = task.compute * station.energy_per_compute
                if station.energy_remaining < energy_cost:
                    reasons.append("not enough energy")
                    continue
                candidates.append(station)

            station = scheduler.choose_station(task, candidates)
            if station is None:
                still_waiting.append(task)
                last_reason[task.task_id] = (
                    reasons[-1] if reasons else "no station can serve this task"
                )
                continue

            energy_cost = task.compute * station.energy_per_compute
            station.step_compute_left -= task.compute
            station.energy_remaining -= energy_cost
            energy_used_by_station[station.station_id] += energy_cost

            transfer_steps = ceil(task.data_size / station.bandwidth)
            communication_delay = station.latency_steps + transfer_steps
            assignments.append(
                Assignment(
                    task=task,
                    station=station,
                    scheduled_step=step,
                    estimated_completion_step=step + communication_delay + 1,
                    energy_used=energy_cost,
                    communication_delay=communication_delay,
                )
            )

        pending = still_waiting

    unassigned = [(task, last_reason.get(task.task_id, "simulation ended")) for task in pending]
    return RunResult(
        scenario_name=scenario.name,
        algorithm_name=scheduler.name,
        time_steps=scenario.time_steps,
        assignments=assignments,
        unassigned=unassigned,
        energy_used_by_station=energy_used_by_station,
        offline_steps_by_station=offline_steps_by_station,
    )
