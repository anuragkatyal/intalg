from __future__ import annotations

import argparse
from pathlib import Path

from pretzel_validation_framework import (
    discover_pretzel_activities,
    render_pretzel_inventory,
    render_validation_result,
    validate_activity,
)
from pretzel_validation_specs import INTALG_ROOT, REGISTERED_SPECS


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate parameterized pretzel activities by enumerating each registered "
            "problem's reachable answer set and checking for overlaps."
        )
    )
    parser.add_argument(
        "activities",
        nargs="*",
        help="Registered activity names to validate.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all registered activities.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List registered activity names and exit.",
    )
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="List every intalg activity file that contains a <pretzel> component.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include per-problem reachable-answer counts in the output.",
    )

    args = parser.parse_args()
    registered_specs_by_path = {
        spec.activity_path.resolve(): name for name, spec in REGISTERED_SPECS.items()
    }
    inventory_entries = discover_pretzel_activities(INTALG_ROOT)

    if args.list:
        for name in sorted(REGISTERED_SPECS):
            print(name)
        return 0

    if args.inventory:
        print(
            render_pretzel_inventory(
                inventory_entries,
                root=INTALG_ROOT,
                registered_specs_by_path=registered_specs_by_path,
            )
        )
        return 0

    if args.all:
        selected_names = sorted(REGISTERED_SPECS)
    else:
        selected_names = args.activities

    if not selected_names:
        parser.error("Specify one or more activity names, or use --all or --list.")

    unknown = [name for name in selected_names if name not in REGISTERED_SPECS]
    if unknown:
        parser.error(
            "Unknown activity name(s): "
            + ", ".join(unknown)
            + ". Use --list to see registered activities."
        )

    exit_code = 0
    for index, name in enumerate(selected_names):
        result = validate_activity(REGISTERED_SPECS[name])
        if index:
            print()
        print(render_validation_result(result, verbose=args.verbose))
        if not result.passed:
            exit_code = 1

    if args.all:
        unregistered_entries = [
            entry
            for entry in inventory_entries
            if entry.activity_path.resolve() not in registered_specs_by_path
        ]
        if unregistered_entries:
            print()
            print(
                render_pretzel_inventory(
                    unregistered_entries,
                    root=INTALG_ROOT,
                    registered_specs_by_path=registered_specs_by_path,
                )
            )
            print(
                "Note: --all validates only registered specs. The unregistered pretzel files above still need activity-specific specs."
            )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())