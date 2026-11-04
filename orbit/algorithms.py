"""Simple interchangeable rules for choosing a computing station."""


class FirstFit:
    name = "First Fit"

    def choose_station(self, task, candidates):
        """Choose the first station in the scenario list that can run the task."""
        return candidates[0] if candidates else None


class BestFit:
    name = "Best Fit"

    def choose_station(self, task, candidates):
        """Choose the fitting station with the least unused compute capacity."""
        if not candidates:
            return None
        return min(candidates, key=lambda station: station.step_compute_left)


class EnergyAware:
    name = "Energy Aware"

    def choose_station(self, task, candidates):
        """Prefer the station that keeps the largest share of its battery."""
        if not candidates:
            return None

        def battery_share_after_task(station):
            energy_cost = task.compute * station.energy_per_compute
            energy_after = station.energy_remaining - energy_cost
            return energy_after / station.energy_capacity

        return max(candidates, key=battery_share_after_task)


ALGORITHMS = {
    "first_fit": FirstFit,
    "best_fit": BestFit,
    "energy_aware": EnergyAware,
}
