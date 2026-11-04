"""Small data models used by the ORBIT simulation."""

from dataclasses import dataclass, field


@dataclass
class Task:
    task_id: str
    name: str
    compute: float
    priority: int
    arrival_step: int
    data_size: float
    min_bandwidth: float


@dataclass
class Station:
    station_id: str
    name: str
    compute_capacity: float
    energy_capacity: float
    energy_remaining: float
    recharge_per_step: float
    energy_per_compute: float
    bandwidth: float
    latency_steps: int
    outage_steps: list[int] = field(default_factory=list)


@dataclass
class Scenario:
    name: str
    time_steps: int
    stations: list[Station]
    tasks: list[Task]


@dataclass
class Assignment:
    task: Task
    station: Station
    scheduled_step: int
    estimated_completion_step: int
    energy_used: float
    communication_delay: int


@dataclass
class RunResult:
    scenario_name: str
    algorithm_name: str
    time_steps: int
    assignments: list[Assignment]
    unassigned: list[tuple[Task, str]]
    energy_used_by_station: dict[str, float]
    offline_steps_by_station: dict[str, int]
