"""Small data models used by the ORBIT simulation."""

from dataclasses import dataclass, field


@dataclass
class Task:
    task_id: str
    name: str
    task_type: str
    compute: float
    duration_steps: int
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
    actual_completion_step: int | None = None


@dataclass
class RunResult:
    scenario_name: str
    algorithm_name: str
    time_steps: int
    assignments: list[Assignment]
    unassigned: list[tuple[Task, str]]
    energy_used_by_station: dict[str, float]
    offline_steps_by_station: dict[str, int]
    steps: list["StepSnapshot"] = field(default_factory=list)
    task_progress: dict[str, "TaskProgress"] = field(default_factory=dict)


@dataclass
class TaskProgress:
    task_id: str
    status: str = "not_arrived"
    station_id: str | None = None
    remaining_steps: int = 0
    scheduled_step: int | None = None
    actual_completion_step: int | None = None
    waiting_reason: str | None = None


@dataclass
class StationStepState:
    station_id: str
    name: str
    online: bool
    compute_capacity: float
    compute_remaining: float
    energy_capacity: float
    energy_remaining: float
    assigned_task_ids: list[str]
    working_task_ids: list[str]


@dataclass
class TaskStepState:
    task_id: str
    task_type: str
    status: str
    station_id: str | None
    remaining_steps: int


@dataclass
class StepSnapshot:
    step: int
    stations: list[StationStepState]
    arrived_task_ids: list[str]
    assigned_task_ids: list[str]
    waiting_task_ids: list[str]
    running_task_ids: list[str] = field(default_factory=list)
    completed_task_ids: list[str] = field(default_factory=list)
    task_states: list[TaskStepState] = field(default_factory=list)
