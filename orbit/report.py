"""Print a readable summary of a simulation run."""


def print_report(result, task_count):
    assigned_count = len(result.assignments)
    completed_count = sum(
        task.status == "completed" for task in result.task_progress.values()
    )
    active_count = sum(
        task.status in {"running", "paused"} for task in result.task_progress.values()
    )
    total_energy = sum(result.energy_used_by_station.values())
    scheduled_rate = 100 * assigned_count / task_count if task_count else 100
    average_delay = (
        sum(item.communication_delay for item in result.assignments) / assigned_count
        if assigned_count
        else 0
    )

    print(f"\n{'=' * 76}")
    print(f"{result.algorithm_name} | Scenario: {result.scenario_name}")
    print(f"{'=' * 76}")
    print(f"Tasks scheduled: {assigned_count}/{task_count} ({scheduled_rate:.0f}%)")
    print(f"Tasks completed: {completed_count}/{task_count}")
    print(f"Tasks still running or paused: {active_count}")
    print(f"Tasks left unscheduled: {len(result.unassigned)}")
    print(f"Energy used: {total_energy:.1f} units")
    print(f"Average communication delay: {average_delay:.1f} steps")

    if result.assignments:
        print("\nAssignments:")
        for item in result.assignments:
            progress = result.task_progress[item.task.task_id]
            actual = (
                f"completed at step {progress.actual_completion_step}"
                if progress.actual_completion_step is not None
                else f"currently {progress.status}, {progress.remaining_steps} work step(s) left"
            )
            print(
                f"  Step {item.scheduled_step}: {item.task.name} "
                f"[{item.task.task_type}, compute {item.task.compute} for "
                f"{item.task.duration_steps} step(s), priority {item.task.priority}] "
                f"-> {item.station.name}; {actual}; "
                f"estimated completion step {item.estimated_completion_step}; "
                f"energy {item.energy_used:.1f}"
            )

    print("\nStation summary:")
    for station_id, energy_used in result.energy_used_by_station.items():
        offline_steps = result.offline_steps_by_station[station_id]
        print(
            f"  {station_id}: {energy_used:.1f} energy used, "
            f"offline for {offline_steps} simulation step(s)"
        )

    if result.unassigned:
        print("\nUnscheduled tasks:")
        for task, reason in result.unassigned:
            print(f"  {task.name}: {reason}")


def print_comparison(results, task_count):
    print(f"ORBIT simulation comparison: {results[0].scenario_name}")
    print("Tasks are prioritized; stations have compute, energy, bandwidth, and outage limits.")
    print(f"Simulation length: {results[0].time_steps} steps")
    print("\nAlgorithm          Scheduled    Completed    Energy used    Avg. comm. delay")
    print("-" * 78)
    for result in results:
        assigned = len(result.assignments)
        completed = sum(
            task.status == "completed" for task in result.task_progress.values()
        )
        energy = sum(result.energy_used_by_station.values())
        delay = (
            sum(item.communication_delay for item in result.assignments) / assigned
            if assigned
            else 0
        )
        print(
            f"{result.algorithm_name:<19} {assigned:>2}/{task_count:<7} "
            f"{completed:>2}/{task_count:<8} {energy:>8.1f} units      {delay:>6.1f} steps"
        )

    for result in results:
        print_report(result, task_count)
