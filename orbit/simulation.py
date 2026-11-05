"""Run the discrete time-step simulation."""

from copy import deepcopy
from math import ceil

from .models import (
    Assignment,
    RunResult,
    StationStepState,
    StepSnapshot,
    TaskProgress,
    TaskStepState,
)


def run_simulation(scenario, scheduler_class):
    """Schedule tasks and advance their execution over simulation steps."""
    stations = deepcopy(scenario.stations)
    tasks = deepcopy(scenario.tasks)
    scheduler = scheduler_class()
    station_by_id = {station.station_id: station for station in stations}
    task_by_id = {task.task_id: task for task in tasks}

    tasks_by_arrival = {}
    for task in tasks:
        tasks_by_arrival.setdefault(task.arrival_step, []).append(task)

    progress = {
        task.task_id: TaskProgress(
            task_id=task.task_id,
            remaining_steps=task.duration_steps,
        )
        for task in tasks
    }
    assignments = []
    assignment_by_task = {}
    pending = []
    last_reason = {}
    energy_used_by_station = {station.station_id: 0.0 for station in stations}
    offline_steps_by_station = {station.station_id: 0 for station in stations}
    step_snapshots = []

    for step in range(scenario.time_steps):
        arrived_tasks = tasks_by_arrival.get(step, [])
        pending.extend(arrived_tasks)
        for task in arrived_tasks:
            progress[task.task_id].status = "waiting"

        # Each station receives a new compute budget and, when online, recharges.
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

        completed_this_step = []

        # Work already assigned gets its compute time before new work is placed.
        running_tasks = [
            task
            for task in tasks
            if progress[task.task_id].status in {"running", "paused"}
        ]
        running_tasks.sort(key=lambda task: task.priority, reverse=True)

        for task in running_tasks:
            task_progress = progress[task.task_id]
            station = station_by_id[task_progress.station_id]

            if station.offline:
                task_progress.status = "paused"
                task_progress.waiting_reason = "station offline"
                continue

            energy_cost = task.compute * station.energy_per_compute
            if station.step_compute_left < task.compute:
                task_progress.status = "paused"
                task_progress.waiting_reason = "station compute is busy"
                continue
            if station.energy_remaining < energy_cost:
                task_progress.status = "paused"
                task_progress.waiting_reason = "station needs more energy"
                continue

            station.step_compute_left -= task.compute
            station.energy_remaining -= energy_cost
            energy_used_by_station[station.station_id] += energy_cost
            assignment = assignment_by_task[task.task_id]
            assignment.energy_used += energy_cost
            task_progress.remaining_steps -= 1
            task_progress.waiting_reason = None

            if task_progress.remaining_steps <= 0:
                task_progress.status = "completed"
                task_progress.actual_completion_step = step
                assignment.actual_completion_step = step
                completed_this_step.append(task.task_id)
            else:
                task_progress.status = "running"

        # Higher-priority waiting tasks are offered to schedulers first.
        pending.sort(key=lambda task: task.priority, reverse=True)
        still_waiting = []
        first_assignment_index = len(assignments)

        for task in pending:
            candidates = []
            reasons = []

            for station in stations:
                if station.offline:
                    reasons.append("station is offline")
                    continue
                if station.step_compute_left < task.compute:
                    reasons.append("not enough compute capacity this step")
                    continue
                if station.bandwidth < task.min_bandwidth:
                    reasons.append("station bandwidth is too low")
                    continue

                energy_cost = task.compute * station.energy_per_compute
                if station.energy_remaining < energy_cost:
                    reasons.append("not enough energy for one work step")
                    continue
                candidates.append(station)

            station = scheduler.choose_station(task, candidates)
            if station is None:
                still_waiting.append(task)
                progress[task.task_id].status = "waiting"
                last_reason[task.task_id] = (
                    reasons[-1] if reasons else "no station can serve this task"
                )
                progress[task.task_id].waiting_reason = last_reason[task.task_id]
                continue

            energy_cost = task.compute * station.energy_per_compute
            station.step_compute_left -= task.compute
            station.energy_remaining -= energy_cost
            energy_used_by_station[station.station_id] += energy_cost

            transfer_steps = ceil(task.data_size / station.bandwidth)
            communication_delay = station.latency_steps + transfer_steps
            task_progress = progress[task.task_id]
            task_progress.station_id = station.station_id
            task_progress.scheduled_step = step
            task_progress.waiting_reason = None
            task_progress.remaining_steps -= 1
            assignment = Assignment(
                task=task,
                station=station,
                scheduled_step=step,
                estimated_completion_step=(
                    step + communication_delay + task.duration_steps
                ),
                energy_used=energy_cost,
                communication_delay=communication_delay,
            )
            assignments.append(assignment)
            assignment_by_task[task.task_id] = assignment

            if task_progress.remaining_steps <= 0:
                task_progress.status = "completed"
                task_progress.actual_completion_step = step
                assignment.actual_completion_step = step
                completed_this_step.append(task.task_id)
            else:
                task_progress.status = "running"
                task_progress.waiting_reason = None

        pending = still_waiting
        step_assignments = assignments[first_assignment_index:]
        step_snapshots.append(
            StepSnapshot(
                step=step,
                stations=[
                    StationStepState(
                        station_id=station.station_id,
                        name=station.name,
                        online=not station.offline,
                        compute_capacity=station.compute_capacity,
                        compute_remaining=(
                            station.step_compute_left if not station.offline else 0
                        ),
                        energy_capacity=station.energy_capacity,
                        energy_remaining=station.energy_remaining,
                        assigned_task_ids=[
                            item.task.task_id
                            for item in step_assignments
                            if item.station.station_id == station.station_id
                        ],
                        working_task_ids=[
                            task.task_id
                            for task in tasks
                            if progress[task.task_id].station_id == station.station_id
                            and progress[task.task_id].status in {"running", "paused"}
                        ],
                    )
                    for station in stations
                ],
                arrived_task_ids=[task.task_id for task in arrived_tasks],
                assigned_task_ids=[item.task.task_id for item in step_assignments],
                waiting_task_ids=[task.task_id for task in pending],
                running_task_ids=[
                    task.task_id
                    for task in tasks
                    if progress[task.task_id].status == "running"
                ],
                completed_task_ids=completed_this_step,
                task_states=[
                    TaskStepState(
                        task_id=task.task_id,
                        task_type=task.task_type,
                        status=progress[task.task_id].status,
                        station_id=progress[task.task_id].station_id,
                        remaining_steps=progress[task.task_id].remaining_steps,
                    )
                    for task in tasks
                ],
            )
        )

    unassigned = []
    for task in pending:
        reason = last_reason.get(task.task_id, "simulation ended before assignment")
        progress[task.task_id].status = "unscheduled"
        progress[task.task_id].waiting_reason = reason
        unassigned.append((task, reason))

    return RunResult(
        scenario_name=scenario.name,
        algorithm_name=scheduler.name,
        time_steps=scenario.time_steps,
        assignments=assignments,
        unassigned=unassigned,
        energy_used_by_station=energy_used_by_station,
        offline_steps_by_station=offline_steps_by_station,
        steps=step_snapshots,
        task_progress=progress,
    )
