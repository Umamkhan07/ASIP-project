"""Serve the local browser dashboard and simulation data."""

from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import webbrowser

from .algorithms import ALGORITHMS
from .scenario import load_scenario
from .simulation import run_simulation


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_PAGE = Path(__file__).resolve().parent / "dashboard" / "index.html"
DEFAULT_SCENARIO = PROJECT_ROOT / "scenarios" / "default.json"


def make_run_data(scenario_path, algorithm_name):
    """Run one scheduler and return only the values the dashboard displays."""
    if algorithm_name not in ALGORITHMS:
        raise ValueError(f"Unknown scheduler: {algorithm_name}")

    scenario = load_scenario(scenario_path)
    result = run_simulation(scenario, ALGORITHMS[algorithm_name])
    assigned_count = len(result.assignments)
    completed_count = sum(
        task.status == "completed" for task in result.task_progress.values()
    )
    return {
        "scenario": {
            "name": scenario.name,
            "time_steps": scenario.time_steps,
            "stations": [asdict(station) for station in scenario.stations],
            "tasks": [asdict(task) for task in scenario.tasks],
        },
        "run": {
            "algorithm": algorithm_name,
            "algorithm_name": result.algorithm_name,
            "assignments": [
                {
                    "task_id": item.task.task_id,
                    "task_name": item.task.name,
                    "task_type": item.task.task_type,
                    "duration_steps": item.task.duration_steps,
                    "priority": item.task.priority,
                    "station_id": item.station.station_id,
                    "station_name": item.station.name,
                    "scheduled_step": item.scheduled_step,
                    "estimated_completion_step": item.estimated_completion_step,
                    "energy_used": item.energy_used,
                    "communication_delay": item.communication_delay,
                    "actual_completion_step": item.actual_completion_step,
                    "status": result.task_progress[item.task.task_id].status,
                    "remaining_steps": result.task_progress[item.task.task_id].remaining_steps,
                }
                for item in result.assignments
            ],
            "unassigned": [
                {"task_id": task.task_id, "name": task.name, "reason": reason}
                for task, reason in result.unassigned
            ],
            "energy_used": sum(result.energy_used_by_station.values()),
            "completed_count": completed_count,
            "average_delay": (
                sum(item.communication_delay for item in result.assignments)
                / assigned_count
                if assigned_count
                else 0
            ),
            "steps": [asdict(step) for step in result.steps],
        },
    }


class DashboardHandler(BaseHTTPRequestHandler):
    """Handle the page request and local simulation data requests."""

    def do_GET(self):
        request = urlsplit(self.path)
        if request.path == "/":
            self.send_file(DASHBOARD_PAGE, "text/html; charset=utf-8")
            return

        if request.path == "/api/simulation":
            query = parse_qs(request.query)
            algorithm = query.get("algorithm", ["best_fit"])[0]
            scenario = query.get("scenario", [str(self.server.scenario_path)])[0]
            try:
                payload = make_run_data(scenario, algorithm)
            except (OSError, ValueError) as error:
                self.send_json({"error": str(error)}, status=400)
                return
            self.send_json(payload)
            return

        self.send_json({"error": "Not found"}, status=404)

    def send_file(self, path, content_type):
        try:
            content = Path(path).read_bytes()
        except OSError:
            self.send_json({"error": "Dashboard page could not be read"}, status=500)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload, status=200):
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string, *args):
        print(f"[ORBIT dashboard] {format_string % args}")


def serve_dashboard(port=8000, scenario_path=DEFAULT_SCENARIO):
    """Open ORBIT's local dashboard and serve it until stopped by the user."""
    if not 1 <= port <= 65535:
        raise ValueError("Dashboard port must be between 1 and 65535")

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    except OSError as error:
        raise ValueError(f"Could not start dashboard on port {port}: {error}") from error

    server.scenario_path = Path(scenario_path).resolve()
    address = f"http://127.0.0.1:{port}"
    print(f"ORBIT dashboard is running at {address}")
    print("Keep this terminal open while using the dashboard. Press Ctrl+C to stop it.")
    webbrowser.open(address)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nORBIT dashboard stopped.")
    finally:
        server.server_close()
