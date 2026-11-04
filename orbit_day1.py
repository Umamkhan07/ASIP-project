"""ORBIT Day 1: a small orbital computing scheduler simulation.

This program compares two simple ways to assign computing tasks to stations.
All capacities are imaginary work units, not real satellite measurements.
"""


def make_stations():
    """Return a fresh set of stations for one scheduling run."""
    return [
        {"name": "Station A", "capacity": 12, "remaining": 12},
        {"name": "Station B", "capacity": 9, "remaining": 9},
        {"name": "Station C", "capacity": 6, "remaining": 6},
    ]


def make_tasks():
    """Return the tasks that need to be assigned."""
    return [
        {"name": "Weather image analysis", "work": 6},
        {"name": "Navigation update", "work": 4},
        {"name": "Sensor data processing", "work": 5},
        {"name": "Orbit calculation", "work": 3},
        {"name": "Detailed terrain scan", "work": 8},
    ]


def assign_first_fit(tasks, stations):
    """Put each task on the first station that has enough capacity."""
    assignments = []
    unassigned_tasks = []

    for task in tasks:
        task_was_assigned = False

        for station in stations:
            if station["remaining"] >= task["work"]:
                station["remaining"] -= task["work"]
                assignments.append((task, station))
                task_was_assigned = True
                break

        if not task_was_assigned:
            unassigned_tasks.append(task)

    return assignments, unassigned_tasks


def assign_best_fit(tasks, stations):
    """Use the station that will have the least space left after a task."""
    assignments = []
    unassigned_tasks = []

    for task in tasks:
        best_station = None

        for station in stations:
            if station["remaining"] >= task["work"]:
                if best_station is None:
                    best_station = station
                elif station["remaining"] < best_station["remaining"]:
                    best_station = station

        if best_station is None:
            unassigned_tasks.append(task)
        else:
            best_station["remaining"] -= task["work"]
            assignments.append((task, best_station))

    return assignments, unassigned_tasks


def print_report(algorithm_name, stations, assignments, unassigned_tasks):
    """Show what the scheduler did and how much capacity remains."""
    print("\n" + "=" * 54)
    print(algorithm_name)
    print("=" * 54)

    if assignments:
        print("\nAssignments:")
        for task, station in assignments:
            print(f"  {task['name']} ({task['work']} units) -> {station['name']}")
    else:
        print("\nNo tasks were assigned.")

    if unassigned_tasks:
        print("\nTasks that did not fit:")
        for task in unassigned_tasks:
            print(f"  {task['name']} ({task['work']} units)")
    else:
        print("\nAll tasks were assigned.")

    print("\nStation capacity remaining:")
    for station in stations:
        used = station["capacity"] - station["remaining"]
        print(
            f"  {station['name']}: {used}/{station['capacity']} units used, "
            f"{station['remaining']} left"
        )

    print(
        f"\nSummary: {len(assignments)} of "
        f"{len(assignments) + len(unassigned_tasks)} tasks assigned."
    )


def main():
    """Ask which scheduling rule to use, then run the simulation."""
    print("ORBIT - Orbital Computing Resource Scheduler")
    print("This small demo assigns tasks while respecting station capacity.")
    print("\nChoose a scheduling algorithm:")
    print("  1. First Fit - use the first station where the task fits")
    print("  2. Best Fit  - use the fitting station with least spare capacity")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        algorithm_name = "First Fit"
        scheduler = assign_first_fit
    elif choice == "2":
        algorithm_name = "Best Fit"
        scheduler = assign_best_fit
    else:
        print("Please run the program again and enter 1 or 2.")
        return

    stations = make_stations()
    tasks = make_tasks()
    assignments, unassigned_tasks = scheduler(tasks, stations)
    print_report(algorithm_name, stations, assignments, unassigned_tasks)


if __name__ == "__main__":
    main()
