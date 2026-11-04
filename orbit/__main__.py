"""Command-line entry point for ORBIT."""

import argparse
from pathlib import Path

from .algorithms import ALGORITHMS
from .report import print_comparison, print_report
from .scenario import load_scenario
from .simulation import run_simulation


def main():
    default_scenario = Path(__file__).resolve().parent.parent / "scenarios" / "default.json"
    parser = argparse.ArgumentParser(description="Simulate orbital computing task scheduling.")
    parser.add_argument(
        "--scenario",
        default=str(default_scenario),
        help="path to a scenario JSON file (default: included demonstration)",
    )
    parser.add_argument(
        "--algorithm",
        choices=["compare", *ALGORITHMS],
        default="compare",
        help="scheduler to use, or compare all schedulers",
    )
    arguments = parser.parse_args()

    try:
        scenario = load_scenario(arguments.scenario)
        if arguments.algorithm == "compare":
            results = [
                run_simulation(scenario, algorithm)
                for algorithm in ALGORITHMS.values()
            ]
            print_comparison(results, len(scenario.tasks))
        else:
            result = run_simulation(scenario, ALGORITHMS[arguments.algorithm])
            print_report(result, len(scenario.tasks))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
