from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from itertools import combinations, permutations, product
from math import gcd
from pathlib import Path
from typing import Callable, Hashable, Iterable, Sequence

from pretzel_validation_framework import (
    ActivitySpec,
    CountSummary,
    ProblemSpace,
    ValidationResult,
    parse_problem_counts,
)


SCRIPTS_DIR = Path(__file__).resolve().parent
INTALG_ROOT = SCRIPTS_DIR.parent


def constant_space(label: str, value: Hashable, description: str = "") -> ProblemSpace:
    return ProblemSpace(
        label=label,
        values_factory=lambda value=value: {value},
        description=description,
    )


def mapped_space(
    label: str,
    domains: Sequence[Iterable[int]],
    mapper: Callable[..., Hashable],
    description: str = "",
) -> ProblemSpace:
    frozen_domains = tuple(tuple(domain) for domain in domains)
    return ProblemSpace(
        label=label,
        values_factory=lambda frozen_domains=frozen_domains, mapper=mapper: {
            mapper(*values) for values in product(*frozen_domains)
        },
        description=description,
    )


def format_complex(value: tuple[int, int]) -> str:
    real, imag = value
    if imag == 0:
        return str(real)
    if real == 0:
        if imag == 1:
            return "i"
        if imag == -1:
            return "-i"
        return f"{imag}i"
    sign = "+" if imag >= 0 else "-"
    imag_abs = abs(imag)
    imag_part = "i" if imag_abs == 1 else f"{imag_abs}i"
    return f"{real}{sign}{imag_part}"


def format_scalar(value: Hashable) -> str:
    return str(value)


def format_fraction(value: Fraction | int) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    return str(value)


def format_decimal(value: float) -> str:
    text = f"{value:.2f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def format_line_expression(slope: Hashable, intercept: Hashable) -> str:
    slope_text = (
        format_decimal(slope)
        if isinstance(slope, float)
        else format_fraction(slope)
    )
    intercept_is_zero = intercept == 0 or intercept == 0.0
    if intercept_is_zero:
        return f"y={slope_text}x"
    intercept_text = (
        format_decimal(intercept)
        if isinstance(intercept, float)
        else format_fraction(intercept)
    )
    sign = "+" if intercept > 0 else ""
    return f"y={slope_text}x{sign}{intercept_text}"


INEQUALITY_VALUES = tuple(value for value in range(-6, 7) if value != 0)
INEQUALITY_DISTRACTOR_VALUES = (7, 8, 9, 10, 11)


def inequality_key(kind: str, value: int | None = None) -> tuple[Hashable, ...]:
    if value is None:
        return (kind,)
    return (kind, value)


def format_inequality(value: Hashable) -> str:
    if not isinstance(value, tuple) or not value:
        return str(value)
    kind = value[0]
    if kind == "all_reals":
        return "(-infinity, infinity)"
    threshold = value[1]
    if kind == "lt":
        return f"x < {threshold}"
    if kind == "le":
        return f"x <= {threshold}"
    if kind == "open_left":
        return f"(-infinity, {threshold})"
    if kind == "closed_right":
        return f"[{threshold}, infinity)"
    if kind == "open_right":
        return f"({threshold}, infinity)"
    return str(value)


SLOPE_INTERCEPT_A_VALUES = tuple(value for value in range(-5, 6) if value != 0)
SLOPE_INTERCEPT_DISTRACTOR_AXIS_VALUES = (6, 7, 8, 9, 10)
SLOPE_INTERCEPT_B_VALUES = tuple(value for value in range(-5, 6) if value != 0)
SLOPE_INTERCEPT_INTERCEPT_VALUES = (6, 7, 8, 9, 10)
SLOPE_INTERCEPT_TOPPING_VALUES = (5, 6, 7, 8, 9)
SLOPE_INTERCEPT_CONST_VALUES = tuple(value for value in range(-5, 6) if value != 0)
SLOPE_INTERCEPT_QUADS = tuple(
    raw
    for raw in permutations(range(2, 10), 4)
    if all(gcd(raw[index1], raw[index2]) == 1 for index1 in range(4) for index2 in range(index1 + 1, 4))
)


def x_const_key(value: int) -> tuple[str, int]:
    return ("x_const", value)


def y_const_key(value: int) -> tuple[str, int]:
    return ("y_const", value)


def line_key(slope: Fraction, intercept: Fraction) -> tuple[str, Fraction, Fraction]:
    return ("line", slope, intercept)


def line_decimal_key(slope: float, intercept: float) -> tuple[str, float, float]:
    return ("line_decimal", slope, intercept)


def format_slope_intercept(value: Hashable) -> str:
    if not isinstance(value, tuple) or not value:
        return str(value)
    kind = value[0]
    if kind == "x_const":
        return f"x={value[1]}"
    if kind == "y_const":
        return f"y={value[1]}"
    if kind == "line":
        return format_line_expression(value[1], value[2])
    if kind == "line_decimal":
        return format_line_expression(value[1], value[2])
    return str(value)


RADICAL_REGULAR_LABELS = [f"problem {index}" for index in range(1, 8)]
RADICAL_DISTRACTOR_DISPLAYS = {
    "problem 8 displayed": 20,
    "problem 9 displayed": -8,
    "problem 10 displayed": 11,
    "problem 11 displayed": -7,
    "problem 12 displayed": 15,
}

POINT_SLOPE_SLOPES = tuple(
    value for value in range(-7, 8) if value not in (-1, 0, 1)
)
POINT_SLOPE_DISTRACTOR_SLOPES = (8, 9, 10, 11)
POINT_SLOPE_COORDS = tuple(value for value in range(-7, 8) if value != 0)
POINT_SLOPE_FUDGES = tuple(value for value in range(-4, 5) if value != 0)
PARALLEL_VALUES = tuple(value for value in range(-6, 7) if value != 0)
TUTORIAL_VALUES = tuple(range(2, 11))


def point_slope_key(y_anchor: int, slope: int, x_anchor: int) -> tuple[int, int, int]:
    return (y_anchor, slope, x_anchor)


def format_point_slope(value: Hashable) -> str:
    if not isinstance(value, tuple) or len(value) != 3:
        return str(value)
    y_anchor, slope, x_anchor = value
    return f"y-({y_anchor})={slope}(x-({x_anchor}))"


def through_point_line(slope: Fraction, x_value: int, y_value: int) -> tuple[str, Fraction, Fraction]:
    return line_key(slope, Fraction(y_value, 1) - slope * x_value)


def through_points_line(
    x_value_1: int, y_value_1: int, x_value_2: int, y_value_2: int
) -> tuple[str, Fraction, Fraction]:
    slope = Fraction(y_value_2 - y_value_1, x_value_2 - x_value_1)
    return line_key(slope, Fraction(y_value_1, 1) - slope * x_value_1)


def format_tutorial_scalar(value: Hashable) -> str:
    if isinstance(value, tuple) and len(value) == 2 and value[0] == "x_eq":
        return f"x={value[1]}"
    return str(value)


def validate_tutorial_circuits_and_pretzels(spec: ActivitySpec) -> ValidationResult:
    errors: list[str] = []

    if not spec.activity_path.exists():
        errors.append(f"Activity file does not exist: {spec.activity_path}")
        counts = CountSummary(
            file_problem_count=0,
            file_distractor_count=0,
            regular_space_count=14,
            distractor_correct_count=2,
            distractor_display_count=2,
        )
        return ValidationResult(
            spec=spec,
            counts=counts,
            errors=tuple(errors),
            overlap_issues=(),
            regular_value_counts=(),
            distractor_correct_value_counts=(),
            distractor_display_value_counts=(),
        )

    file_problem_count, file_distractor_count = parse_problem_counts(spec.activity_path)
    counts = CountSummary(
        file_problem_count=file_problem_count,
        file_distractor_count=file_distractor_count,
        regular_space_count=14,
        distractor_correct_count=2,
        distractor_display_count=2,
    )

    if spec.expected_problem_count is not None and file_problem_count != spec.expected_problem_count:
        errors.append(
            f"Expected {spec.expected_problem_count} <problem> tags, found {file_problem_count}."
        )
    if spec.expected_distractor_count is not None and file_distractor_count != spec.expected_distractor_count:
        errors.append(
            f"Expected {spec.expected_distractor_count} distractors, found {file_distractor_count}."
        )

    regular_value_counts = tuple(
        [(f"pretzel1 problem {index}", len(TUTORIAL_VALUES)) for index in range(1, 7)]
        + [(f"pretzel2 problem {index}", len(TUTORIAL_VALUES)) for index in range(1, 5)]
        + [(f"pretzel3 problem {index}", len(TUTORIAL_VALUES)) for index in range(1, 5)]
    )
    distractor_correct_value_counts = (
        ("pretzel3 problem 5 correct", len(TUTORIAL_VALUES)),
        ("pretzel3 problem 6 correct", len(TUTORIAL_VALUES)),
    )
    distractor_display_value_counts = (
        ("pretzel3 problem 5 displayed", len(TUTORIAL_VALUES)),
        ("pretzel3 problem 6 displayed", len(TUTORIAL_VALUES)),
    )

    for final_answers in permutations(TUTORIAL_VALUES, 6):
        pretzel1_displayed = [("x_eq", value) for value in final_answers]
        if len(set(pretzel1_displayed)) != 6:
            errors.append("Pretzel 1 has a repeated displayed answer in at least one scenario.")
            break

        pretzel3_regular = [("x_eq", final_answers[index]) for index in range(4)]
        pretzel3_correct = [("x_eq", final_answers[4]), ("x_eq", final_answers[5])]
        pretzel3_display = [
            ("x_eq", final_answers[4] + 20),
            ("x_eq", final_answers[5] + 40),
        ]
        if len(set(pretzel3_regular + pretzel3_correct)) != 6:
            errors.append(
                "Pretzel 3 has a distractor true answer overlapping a regular answer in at least one scenario."
            )
            break
        if len(set(pretzel3_regular + pretzel3_display)) != 6:
            errors.append(
                "Pretzel 3 has a displayed distractor answer overlapping a regular answer in at least one scenario."
            )
            break
        if len(set(pretzel3_display + pretzel3_correct)) != 4:
            errors.append(
                "Pretzel 3 has a displayed distractor answer overlapping a distractor true answer in at least one scenario."
            )
            break

    for final_answers in permutations(TUTORIAL_VALUES, 4):
        pretzel2_displayed = [("x_eq", value) for value in final_answers]
        if len(set(pretzel2_displayed)) != 4:
            errors.append("Pretzel 2 has a repeated displayed answer in at least one scenario.")
            break

    return ValidationResult(
        spec=spec,
        counts=counts,
        errors=tuple(errors),
        overlap_issues=(),
        regular_value_counts=regular_value_counts,
        distractor_correct_value_counts=distractor_correct_value_counts,
        distractor_display_value_counts=distractor_display_value_counts,
    )


def parallel_signature_compatible(
    left_signature: tuple[tuple[str, int], ...],
    right_signature: tuple[tuple[str, int], ...],
) -> bool:
    combined: dict[str, int] = {}
    for slot, value in left_signature + right_signature:
        existing = combined.get(slot)
        if existing is not None and existing != value:
            return False
        combined[slot] = value

    for prefix in ("m", "x", "y"):
        seen_values: dict[int, str] = {}
        for slot, value in combined.items():
            if not slot.startswith(prefix):
                continue
            other_slot = seen_values.get(value)
            if other_slot is not None and other_slot != slot:
                return False
            seen_values[value] = slot
    return True


def build_parallel_line_family_map(
    m_slots: Sequence[str],
    x_slots: Sequence[str],
    y_slots: Sequence[str],
    evaluator: Callable[[dict[str, int]], Hashable],
) -> dict[Hashable, list[tuple[tuple[str, int], ...]]]:
    line_map: dict[Hashable, list[tuple[tuple[str, int], ...]]] = defaultdict(list)
    for m_values in permutations(PARALLEL_VALUES, len(m_slots)):
        m_assignment = dict(zip(m_slots, m_values))
        for x_values in permutations(PARALLEL_VALUES, len(x_slots)):
            x_assignment = dict(zip(x_slots, x_values))
            for y_values in permutations(PARALLEL_VALUES, len(y_slots)):
                assignment = dict(m_assignment)
                assignment.update(x_assignment)
                assignment.update(zip(y_slots, y_values))
                signature = tuple(sorted(assignment.items()))
                line_map[evaluator(assignment)].append(signature)
    return line_map


def find_parallel_collision_example(
    left_map: dict[Hashable, list[tuple[tuple[str, int], ...]]],
    right_map: dict[Hashable, list[tuple[tuple[str, int], ...]]],
) -> Hashable | None:
    for line in left_map.keys() & right_map.keys():
        for left_signature in left_map[line]:
            for right_signature in right_map[line]:
                if parallel_signature_compatible(left_signature, right_signature):
                    return line
    return None


def validate_parallel_perpendicular_lines(spec: ActivitySpec) -> ValidationResult:
    errors: list[str] = []

    if not spec.activity_path.exists():
        errors.append(f"Activity file does not exist: {spec.activity_path}")
        counts = CountSummary(
            file_problem_count=0,
            file_distractor_count=0,
            regular_space_count=10,
            distractor_correct_count=6,
            distractor_display_count=6,
        )
        return ValidationResult(
            spec=spec,
            counts=counts,
            errors=tuple(errors),
            overlap_issues=(),
            regular_value_counts=(),
            distractor_correct_value_counts=(),
            distractor_display_value_counts=(),
        )

    file_problem_count, file_distractor_count = parse_problem_counts(spec.activity_path)
    counts = CountSummary(
        file_problem_count=file_problem_count,
        file_distractor_count=file_distractor_count,
        regular_space_count=10,
        distractor_correct_count=6,
        distractor_display_count=6,
    )

    if spec.expected_problem_count is not None and file_problem_count != spec.expected_problem_count:
        errors.append(
            f"Expected {spec.expected_problem_count} <problem> tags, found {file_problem_count}."
        )
    if spec.expected_distractor_count is not None and file_distractor_count != spec.expected_distractor_count:
        errors.append(
            f"Expected {spec.expected_distractor_count} distractors, found {file_distractor_count}."
        )

    regular_families = {
        "problem 1": build_parallel_line_family_map(
            ("m1",),
            ("x1",),
            ("y1",),
            lambda assignment: through_point_line(
                Fraction(assignment["m1"], 1), assignment["x1"], assignment["y1"]
            ),
        ),
        "problem 2": build_parallel_line_family_map(
            ("m1",),
            ("x2",),
            ("y2",),
            lambda assignment: through_point_line(
                Fraction(-1, assignment["m1"]), assignment["x2"], assignment["y2"] + 800
            ),
        ),
        "problem 3": build_parallel_line_family_map(
            (),
            ("x1", "x2"),
            ("y1", "y2"),
            lambda assignment: through_points_line(
                assignment["x1"],
                assignment["y1"] + 200,
                assignment["x2"],
                assignment["y2"] + 200,
            ),
        ),
        "problem 4": build_parallel_line_family_map(
            ("m2",),
            ("x3",),
            ("y3",),
            lambda assignment: through_point_line(
                Fraction(-1, assignment["m2"]), assignment["x3"], assignment["y3"] + 1000
            ),
        ),
        "problem 5": build_parallel_line_family_map(
            ("m3",),
            ("x4",),
            ("y4",),
            lambda assignment: through_point_line(
                Fraction(assignment["m3"], 1), assignment["x4"], assignment["y4"]
            ),
        ),
        "problem 6": build_parallel_line_family_map(
            (),
            ("x3", "x5"),
            ("y3", "y5"),
            lambda assignment: through_points_line(
                assignment["x3"],
                assignment["y3"] + 400,
                assignment["x5"],
                assignment["y5"] + 400,
            ),
        ),
        "problem 7": build_parallel_line_family_map(
            ("m4",),
            ("x5",),
            ("y5",),
            lambda assignment: through_point_line(
                Fraction(1, assignment["m4"]), assignment["x5"], assignment["y5"] + 1200
            ),
        ),
        "problem 8": build_parallel_line_family_map(
            ("m5",),
            ("x6",),
            ("y6",),
            lambda assignment: through_point_line(
                Fraction(assignment["m5"], 1), assignment["x6"], assignment["y6"]
            ),
        ),
        "problem 9": build_parallel_line_family_map(
            ("m6",),
            ("x1",),
            ("y1",),
            lambda assignment: through_point_line(
                Fraction(assignment["m6"], 1), assignment["x1"], assignment["y1"]
            ),
        ),
        "problem 10": build_parallel_line_family_map(
            ("m7",),
            ("x2",),
            ("y2",),
            lambda assignment: through_point_line(
                Fraction(-1, assignment["m7"]), assignment["x2"], assignment["y2"] + 1400
            ),
        ),
    }

    distractor_correct_families = {
        "problem 11 correct": build_parallel_line_family_map(
            ("m1",),
            (),
            (),
            lambda assignment: through_point_line(
                Fraction(-1, assignment["m1"]), 0, 2000
            ),
        ),
        "problem 12 correct": build_parallel_line_family_map(
            ("m2",),
            (),
            (),
            lambda assignment: through_point_line(
                Fraction(-1, assignment["m2"]), 0, 2200
            ),
        ),
        "problem 13 correct": build_parallel_line_family_map(
            ("m3",),
            (),
            (),
            lambda assignment: through_point_line(
                Fraction(assignment["m3"], 1), 1, 2400
            ),
        ),
        "problem 14 correct": build_parallel_line_family_map(
            ("m4",),
            (),
            (),
            lambda assignment: through_point_line(
                Fraction(assignment["m4"], 1), 0, 2600
            ),
        ),
        "problem 15 correct": build_parallel_line_family_map(
            (),
            ("x5", "x6"),
            ("y5", "y6"),
            lambda assignment: through_points_line(
                assignment["x5"],
                assignment["y5"] + 3000,
                assignment["x6"],
                assignment["y6"] + 3000,
            ),
        ),
        "problem 16 correct": build_parallel_line_family_map(
            ("m6",),
            (),
            (),
            lambda assignment: line_key(Fraction(-1, assignment["m6"]), Fraction(3400, 1)),
        ),
    }

    distractor_display_families = {
        "problem 11 displayed": build_parallel_line_family_map(
            ("m1",),
            (),
            (),
            lambda assignment: through_point_line(
                Fraction(assignment["m1"], 1), 0, 2000
            ),
        ),
        "problem 12 displayed": build_parallel_line_family_map(
            ("m2",),
            (),
            (),
            lambda assignment: through_point_line(
                Fraction(1, assignment["m2"]), 0, 2200
            ),
        ),
        "problem 13 displayed": build_parallel_line_family_map(
            ("m3",),
            (),
            (),
            lambda assignment: line_key(
                Fraction(assignment["m3"], 1),
                Fraction(2400 + assignment["m3"], 1),
            ),
        ),
        "problem 14 displayed": build_parallel_line_family_map(
            ("m4",),
            (),
            (),
            lambda assignment: through_point_line(
                Fraction(assignment["m4"], 1), 0, 2800
            ),
        ),
        "problem 15 displayed": build_parallel_line_family_map(
            (),
            ("x5", "x6"),
            ("y5", "y6"),
            lambda assignment: line_key(
                Fraction(assignment["x6"] - assignment["x5"], assignment["y6"] - assignment["y5"]),
                Fraction(3200, 1),
            ),
        ),
        "problem 16 displayed": build_parallel_line_family_map(
            ("m6",),
            (),
            (),
            lambda assignment: line_key(Fraction(1, assignment["m6"]), Fraction(3400, 1)),
        ),
    }

    regular_labels = tuple(regular_families)
    distractor_correct_labels = tuple(distractor_correct_families)
    distractor_display_labels = tuple(distractor_display_families)

    for left_label, right_label in combinations(regular_labels, 2):
        collision = find_parallel_collision_example(
            regular_families[left_label], regular_families[right_label]
        )
        if collision is not None:
            errors.append(
                f"{left_label} overlaps {right_label}. Example: {format_slope_intercept(collision)}"
            )
            break

    if not errors:
        for distractor_label in distractor_correct_labels:
            for regular_label in regular_labels:
                collision = find_parallel_collision_example(
                    distractor_correct_families[distractor_label], regular_families[regular_label]
                )
                if collision is not None:
                    errors.append(
                        f"{distractor_label} overlaps {regular_label}. Example: {format_slope_intercept(collision)}"
                    )
                    break
            if errors:
                break

    if not errors:
        for distractor_label in distractor_display_labels:
            for regular_label in regular_labels:
                collision = find_parallel_collision_example(
                    distractor_display_families[distractor_label], regular_families[regular_label]
                )
                if collision is not None:
                    errors.append(
                        f"{distractor_label} overlaps {regular_label}. Example: {format_slope_intercept(collision)}"
                    )
                    break
            if errors:
                break

    if not errors:
        for distractor_label, family_map in distractor_display_families.items():
            for correct_label, correct_map in distractor_correct_families.items():
                collision = find_parallel_collision_example(family_map, correct_map)
                if collision is not None:
                    errors.append(
                        f"{distractor_label} overlaps {correct_label}. Example: {format_slope_intercept(collision)}"
                    )
                    break
            if errors:
                break

    if not errors:
        for left_label, right_label in combinations(distractor_display_labels, 2):
            collision = find_parallel_collision_example(
                distractor_display_families[left_label], distractor_display_families[right_label]
            )
            if collision is not None:
                errors.append(
                    f"{left_label} overlaps {right_label}. Example: {format_slope_intercept(collision)}"
                )
                break

    regular_value_counts = tuple(
        (label, len(family_map)) for label, family_map in regular_families.items()
    )
    distractor_correct_value_counts = tuple(
        (label, len(family_map)) for label, family_map in distractor_correct_families.items()
    )
    distractor_display_value_counts = tuple(
        (label, len(family_map)) for label, family_map in distractor_display_families.items()
    )

    return ValidationResult(
        spec=spec,
        counts=counts,
        errors=tuple(errors),
        overlap_issues=(),
        regular_value_counts=regular_value_counts,
        distractor_correct_value_counts=distractor_correct_value_counts,
        distractor_display_value_counts=distractor_display_value_counts,
    )


def find_point_slope_display_collision_examples() -> list[str]:
    errors: list[str] = []

    for x1 in POINT_SLOPE_COORDS:
        for y1 in POINT_SLOPE_COORDS:
            if y1 == x1:
                continue

            for fudge in POINT_SLOPE_FUDGES:
                regular = point_slope_key(-y1 - fudge, POINT_SLOPE_SLOPES[0], -x1 + fudge)
                distractor = point_slope_key(y1 + fudge, POINT_SLOPE_DISTRACTOR_SLOPES[0], -x1 + fudge)
                if regular[0] == distractor[0] and regular[2] == distractor[2]:
                    pass

            for fudge in POINT_SLOPE_FUDGES:
                for distractor_slope in POINT_SLOPE_DISTRACTOR_SLOPES:
                    if point_slope_key(-y1, POINT_SLOPE_SLOPES[0], -x1) == point_slope_key(
                        y1 - fudge * distractor_slope,
                        POINT_SLOPE_SLOPES[0],
                        x1 - fudge,
                    ):
                        errors.append(
                            "Problem 7 displayed answers overlap problem 2. Example: "
                            f"{format_point_slope(point_slope_key(-y1, POINT_SLOPE_SLOPES[0], -x1))}"
                        )
                        return errors

            for fudge in POINT_SLOPE_FUDGES:
                for distractor_slope in POINT_SLOPE_DISTRACTOR_SLOPES:
                    if point_slope_key(-y1, POINT_SLOPE_SLOPES[0], -x1) == point_slope_key(
                        y1 + fudge * distractor_slope,
                        POINT_SLOPE_SLOPES[0],
                        -x1 - fudge,
                    ):
                        errors.append(
                            "Problem 8 displayed answers overlap problem 4. Example: "
                            f"{format_point_slope(point_slope_key(-y1, POINT_SLOPE_SLOPES[0], -x1))}"
                        )
                        return errors

            for fudge in POINT_SLOPE_FUDGES:
                for slope in POINT_SLOPE_SLOPES:
                    for distractor_slope in POINT_SLOPE_DISTRACTOR_SLOPES:
                        if point_slope_key(-y1 - fudge, slope, -x1 + fudge) == point_slope_key(
                            y1 + fudge,
                            distractor_slope,
                            -x1 + fudge,
                        ):
                            errors.append(
                                "Problem 9 displayed answers overlap problem 5. Example: "
                                f"{format_point_slope(point_slope_key(-y1 - fudge, slope, -x1 + fudge))}"
                            )
                            return errors

            for slope in POINT_SLOPE_SLOPES:
                if point_slope_key(-y1, slope, -x1) == point_slope_key(-y1, slope, x1):
                    errors.append(
                        "Problem 10 displayed answers overlap problem 6. Example: "
                        f"{format_point_slope(point_slope_key(-y1, slope, -x1))}"
                    )
                    return errors

    return errors


def validate_linear_inequalities(spec: ActivitySpec) -> ValidationResult:
    errors: list[str] = []

    if not spec.activity_path.exists():
        errors.append(f"Activity file does not exist: {spec.activity_path}")
        counts = CountSummary(
            file_problem_count=0,
            file_distractor_count=0,
            regular_space_count=7,
            distractor_correct_count=1,
            distractor_display_count=1,
        )
        return ValidationResult(
            spec=spec,
            counts=counts,
            errors=tuple(errors),
            overlap_issues=(),
            regular_value_counts=(),
            distractor_correct_value_counts=(),
            distractor_display_value_counts=(),
        )

    file_problem_count, file_distractor_count = parse_problem_counts(spec.activity_path)
    counts = CountSummary(
        file_problem_count=file_problem_count,
        file_distractor_count=file_distractor_count,
        regular_space_count=7,
        distractor_correct_count=1,
        distractor_display_count=1,
    )

    if spec.expected_problem_count is not None and file_problem_count != spec.expected_problem_count:
        errors.append(
            f"Expected {spec.expected_problem_count} <problem> tags, found {file_problem_count}."
        )
    if spec.expected_distractor_count is not None and file_distractor_count != spec.expected_distractor_count:
        errors.append(
            f"Expected {spec.expected_distractor_count} distractors, found {file_distractor_count}."
        )

    regular_sets = {
        "problem 1": {inequality_key("lt", value) for value in INEQUALITY_VALUES},
        "problem 2": {inequality_key("le", value) for value in INEQUALITY_VALUES},
        "problem 3": {inequality_key("open_left", value) for value in INEQUALITY_VALUES},
        "problem 4": {inequality_key("open_left", value) for value in INEQUALITY_VALUES},
        "problem 5": {inequality_key("closed_right", value) for value in INEQUALITY_VALUES},
        "problem 7": {inequality_key("lt", value) for value in INEQUALITY_VALUES},
        "problem 8": {inequality_key("open_right", value) for value in INEQUALITY_VALUES},
    }
    distractor_display_sets = {
        "problem 6 displayed": {
            inequality_key("closed_right", value) for value in INEQUALITY_VALUES
        }
    }
    distractor_correct_sets = {
        "problem 6 correct": {inequality_key("all_reals")}
        | {inequality_key("le", value) for value in INEQUALITY_DISTRACTOR_VALUES}
        | {
            inequality_key("closed_right", value)
            for value in INEQUALITY_DISTRACTOR_VALUES
        }
    }

    regular_union = set().union(*regular_sets.values())
    distractor_correct_union = set().union(*distractor_correct_sets.values())
    if regular_union & distractor_correct_union:
        example = next(iter(regular_union & distractor_correct_union))
        errors.append(
            "The distractor true-answer family overlaps a regular displayed answer. "
            f"Example: {format_inequality(example)}"
        )

    regular_value_counts = tuple(
        (label, len(values)) for label, values in regular_sets.items()
    )
    distractor_correct_value_counts = tuple(
        (label, len(values)) for label, values in distractor_correct_sets.items()
    )
    distractor_display_value_counts = tuple(
        (label, len(values)) for label, values in distractor_display_sets.items()
    )

    return ValidationResult(
        spec=spec,
        counts=counts,
        errors=tuple(errors),
        overlap_issues=(),
        regular_value_counts=regular_value_counts,
        distractor_correct_value_counts=distractor_correct_value_counts,
        distractor_display_value_counts=distractor_display_value_counts,
    )


def validate_slope_intercept_form(spec: ActivitySpec) -> ValidationResult:
    errors: list[str] = []

    if not spec.activity_path.exists():
        errors.append(f"Activity file does not exist: {spec.activity_path}")
        counts = CountSummary(
            file_problem_count=0,
            file_distractor_count=0,
            regular_space_count=10,
            distractor_correct_count=2,
            distractor_display_count=2,
        )
        return ValidationResult(
            spec=spec,
            counts=counts,
            errors=tuple(errors),
            overlap_issues=(),
            regular_value_counts=(),
            distractor_correct_value_counts=(),
            distractor_display_value_counts=(),
        )

    file_problem_count, file_distractor_count = parse_problem_counts(spec.activity_path)
    counts = CountSummary(
        file_problem_count=file_problem_count,
        file_distractor_count=file_distractor_count,
        regular_space_count=10,
        distractor_correct_count=2,
        distractor_display_count=2,
    )

    if spec.expected_problem_count is not None and file_problem_count != spec.expected_problem_count:
        errors.append(
            f"Expected {spec.expected_problem_count} <problem> tags, found {file_problem_count}."
        )
    if spec.expected_distractor_count is not None and file_distractor_count != spec.expected_distractor_count:
        errors.append(
            f"Expected {spec.expected_distractor_count} distractors, found {file_distractor_count}."
        )

    regular_sets = {
        "problem 1": {y_const_key(value) for value in SLOPE_INTERCEPT_A_VALUES},
        "problem 2": {
            line_key(-Fraction(y_intercept, x_intercept), Fraction(y_intercept, 1))
            for x_intercept in SLOPE_INTERCEPT_INTERCEPT_VALUES
            for y_intercept in SLOPE_INTERCEPT_INTERCEPT_VALUES
            if x_intercept != y_intercept
        },
        "problem 3": {
            line_key(Fraction(raw[0], raw[1]), Fraction(intercept, 1))
            for raw in SLOPE_INTERCEPT_QUADS
            for intercept in SLOPE_INTERCEPT_B_VALUES
        },
        "problem 4": {
            line_decimal_key(round(delta / (2026 - year), 2), 0.0)
            for delta in range(5050, 10001, 90)
            for year in range(2010, 2021)
        },
        "problem 5": {x_const_key(value) for value in SLOPE_INTERCEPT_A_VALUES},
        "problem 6": {
            line_key(Fraction(value, 1), Fraction(14, 1))
            for value in SLOPE_INTERCEPT_TOPPING_VALUES
        },
        "problem 7": {y_const_key(value) for value in SLOPE_INTERCEPT_A_VALUES},
        "problem 8": {x_const_key(value) for value in SLOPE_INTERCEPT_A_VALUES},
        "problem 9": {
            line_key(Fraction(raw[2], raw[3]), Fraction(constant, raw[3]))
            for raw in SLOPE_INTERCEPT_QUADS
            for constant in SLOPE_INTERCEPT_CONST_VALUES
        },
        "problem 10": {
            line_key(-Fraction(raw[0], raw[1]), Fraction(intercept, 1))
            for raw in SLOPE_INTERCEPT_QUADS
            for intercept in SLOPE_INTERCEPT_B_VALUES
        },
    }
    distractor_correct_sets = {
        "problem 11 correct": {
            y_const_key(value) for value in SLOPE_INTERCEPT_DISTRACTOR_AXIS_VALUES
        },
        "problem 12 correct": {
            x_const_key(value) for value in SLOPE_INTERCEPT_DISTRACTOR_AXIS_VALUES
        },
    }
    distractor_display_sets = {
        "problem 11 displayed": {x_const_key(value) for value in SLOPE_INTERCEPT_A_VALUES},
        "problem 12 displayed": {y_const_key(value) for value in SLOPE_INTERCEPT_A_VALUES},
    }

    for a1, a2, a3 in permutations(SLOPE_INTERCEPT_A_VALUES, 3):
        displayed = {
            "problem 1": y_const_key(a1),
            "problem 5": x_const_key(a3),
            "problem 7": y_const_key(a3),
            "problem 8": x_const_key(a2),
            "problem 11 displayed": x_const_key(a1),
            "problem 12 displayed": y_const_key(a2),
        }
        inverse: dict[Hashable, list[str]] = defaultdict(list)
        for label, value in displayed.items():
            inverse[value].append(label)
        duplicate_examples = {
            value: labels for value, labels in inverse.items() if len(labels) > 1
        }
        if duplicate_examples:
            value, labels = next(iter(duplicate_examples.items()))
            errors.append(
                "A same-scenario constant-answer collision was found. "
                f"Example: {format_slope_intercept(value)} appears in {', '.join(labels)}."
            )
            break

    for raw in SLOPE_INTERCEPT_QUADS:
        slope1 = Fraction(raw[0], raw[1])
        slope3 = Fraction(raw[2], raw[3])
        if slope1 != slope3:
            continue
        for intercept in SLOPE_INTERCEPT_B_VALUES:
            for constant in SLOPE_INTERCEPT_CONST_VALUES:
                if Fraction(intercept, 1) == Fraction(constant, raw[3]):
                    errors.append(
                        "Problem 3 and problem 9 can coincide in the same top-level slope scenario. "
                        f"Example: {format_slope_intercept(line_key(slope1, Fraction(intercept, 1)))}"
                    )
                    break
            if errors and errors[-1].startswith("Problem 3 and problem 9"):
                break
        if errors and errors[-1].startswith("Problem 3 and problem 9"):
            break

    line_problem_labels = ["problem 2", "problem 3", "problem 4", "problem 6", "problem 9", "problem 10"]
    for left_label, right_label in combinations(line_problem_labels, 2):
        if {left_label, right_label} == {"problem 3", "problem 9"}:
            continue
        overlap = regular_sets[left_label] & regular_sets[right_label]
        if overlap:
            example = next(iter(overlap))
            errors.append(
                f"{left_label} overlaps {right_label}. Example: {format_slope_intercept(example)}"
            )
            break

    regular_union = set().union(*regular_sets.values())
    distractor_correct_union = set().union(*distractor_correct_sets.values())
    overlap = regular_union & distractor_correct_union
    if overlap:
        example = next(iter(overlap))
        errors.append(
            "A distractor correct answer overlaps a regular displayed answer. "
            f"Example: {format_slope_intercept(example)}"
        )

    regular_value_counts = tuple(
        (label, len(values)) for label, values in regular_sets.items()
    )
    distractor_correct_value_counts = tuple(
        (label, len(values)) for label, values in distractor_correct_sets.items()
    )
    distractor_display_value_counts = tuple(
        (label, len(values)) for label, values in distractor_display_sets.items()
    )

    return ValidationResult(
        spec=spec,
        counts=counts,
        errors=tuple(errors),
        overlap_issues=(),
        regular_value_counts=regular_value_counts,
        distractor_correct_value_counts=distractor_correct_value_counts,
        distractor_display_value_counts=distractor_display_value_counts,
    )


def validate_point_slope_form(spec: ActivitySpec) -> ValidationResult:
    errors: list[str] = []

    if not spec.activity_path.exists():
        errors.append(f"Activity file does not exist: {spec.activity_path}")
        counts = CountSummary(
            file_problem_count=0,
            file_distractor_count=0,
            regular_space_count=6,
            distractor_correct_count=4,
            distractor_display_count=4,
        )
        return ValidationResult(
            spec=spec,
            counts=counts,
            errors=tuple(errors),
            overlap_issues=(),
            regular_value_counts=(),
            distractor_correct_value_counts=(),
            distractor_display_value_counts=(),
        )

    file_problem_count, file_distractor_count = parse_problem_counts(spec.activity_path)
    counts = CountSummary(
        file_problem_count=file_problem_count,
        file_distractor_count=file_distractor_count,
        regular_space_count=6,
        distractor_correct_count=4,
        distractor_display_count=4,
    )

    if spec.expected_problem_count is not None and file_problem_count != spec.expected_problem_count:
        errors.append(
            f"Expected {spec.expected_problem_count} <problem> tags, found {file_problem_count}."
        )
    if spec.expected_distractor_count is not None and file_distractor_count != spec.expected_distractor_count:
        errors.append(
            f"Expected {spec.expected_distractor_count} distractors, found {file_distractor_count}."
        )

    regular_sets = {
        "problem 1": {
            point_slope_key(y1, slope, x1)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for slope in POINT_SLOPE_SLOPES
        },
        "problem 2": {
            point_slope_key(-y1, slope, -x1)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for slope in POINT_SLOPE_SLOPES
        },
        "problem 3": {
            point_slope_key(y1 + fudge * slope, slope, x1 + fudge)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for fudge in POINT_SLOPE_FUDGES
            for slope in POINT_SLOPE_SLOPES
        },
        "problem 4": {
            point_slope_key(-y1, slope, -x1)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for slope in POINT_SLOPE_SLOPES
        },
        "problem 5": {
            point_slope_key(-y1 - fudge, slope, -x1 + fudge)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for fudge in POINT_SLOPE_FUDGES
            for slope in POINT_SLOPE_SLOPES
        },
        "problem 6": {
            point_slope_key(-y1, slope, -x1)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for slope in POINT_SLOPE_SLOPES
        },
    }

    distractor_correct_sets = {
        "problem 7 correct": {
            point_slope_key(-y1, slope, -x1)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for slope in POINT_SLOPE_DISTRACTOR_SLOPES
        },
        "problem 8 correct": {
            point_slope_key(y1, slope, x1)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for slope in POINT_SLOPE_DISTRACTOR_SLOPES
        },
        "problem 9 correct": {
            point_slope_key(-y1, -slope, -x1)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for slope in POINT_SLOPE_DISTRACTOR_SLOPES
        },
        "problem 10 correct": {
            point_slope_key(-y1, slope, -x1)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for slope in POINT_SLOPE_DISTRACTOR_SLOPES
        },
    }

    distractor_display_sets = {
        "problem 7 displayed": {
            point_slope_key(y1 - fudge * distractor_slope, slope, x1 - fudge)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for fudge in POINT_SLOPE_FUDGES
            for slope in POINT_SLOPE_SLOPES
            for distractor_slope in POINT_SLOPE_DISTRACTOR_SLOPES
        },
        "problem 8 displayed": {
            point_slope_key(y1 + fudge * distractor_slope, slope, -x1 - fudge)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for fudge in POINT_SLOPE_FUDGES
            for slope in POINT_SLOPE_SLOPES
            for distractor_slope in POINT_SLOPE_DISTRACTOR_SLOPES
        },
        "problem 9 displayed": {
            point_slope_key(y1 + fudge, distractor_slope, -x1 + fudge)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for fudge in POINT_SLOPE_FUDGES
            for distractor_slope in POINT_SLOPE_DISTRACTOR_SLOPES
        },
        "problem 10 displayed": {
            point_slope_key(-y1, slope, x1)
            for x1 in POINT_SLOPE_COORDS
            for y1 in POINT_SLOPE_COORDS
            if y1 != x1
            for slope in POINT_SLOPE_SLOPES
        },
    }

    errors.extend(find_point_slope_display_collision_examples())

    regular_slopes = set(POINT_SLOPE_SLOPES)
    distractor_correct_slopes = set(POINT_SLOPE_DISTRACTOR_SLOPES) | {
        -value for value in POINT_SLOPE_DISTRACTOR_SLOPES
    }
    if regular_slopes & distractor_correct_slopes:
        errors.append("Distractor correct slope domains overlap the regular slope domain.")

    regular_value_counts = tuple(
        (label, len(values)) for label, values in regular_sets.items()
    )
    distractor_correct_value_counts = tuple(
        (label, len(values)) for label, values in distractor_correct_sets.items()
    )
    distractor_display_value_counts = tuple(
        (label, len(values)) for label, values in distractor_display_sets.items()
    )

    return ValidationResult(
        spec=spec,
        counts=counts,
        errors=tuple(errors),
        overlap_issues=(),
        regular_value_counts=regular_value_counts,
        distractor_correct_value_counts=distractor_correct_value_counts,
        distractor_display_value_counts=distractor_display_value_counts,
    )


def iter_radical_solution_assignments() -> Iterable[dict[str, int]]:
    for solution1 in range(1, 6):
        for solution2 in range(1, 6):
            if solution2 == solution1:
                continue
            for solution4 in range(1, 6):
                if solution4 in {solution1, solution2}:
                    continue
                for solution3 in range(1, 7):
                    if solution3 in {solution1, solution2, solution4}:
                        continue
                    for solution6 in range(3, 8):
                        if solution6 in {solution1, solution2, solution3, solution4}:
                            continue
                        for solution5 in range(3, 11):
                            if solution5 in {
                                solution1,
                                solution2,
                                solution3,
                                solution4,
                                solution6,
                            }:
                                continue
                            for solution7 in range(-13, -8):
                                yield {
                                    "problem 1": solution1,
                                    "problem 2": solution2,
                                    "problem 3": solution3,
                                    "problem 4": solution4,
                                    "problem 5": solution5,
                                    "problem 6": solution6,
                                    "problem 7": solution7,
                                }


def validate_radical_equations(spec: ActivitySpec) -> ValidationResult:
    errors: list[str] = []

    if not spec.activity_path.exists():
        errors.append(f"Activity file does not exist: {spec.activity_path}")
        counts = CountSummary(
            file_problem_count=0,
            file_distractor_count=0,
            regular_space_count=7,
            distractor_correct_count=5,
            distractor_display_count=5,
        )
        return ValidationResult(
            spec=spec,
            counts=counts,
            errors=tuple(errors),
            overlap_issues=(),
            regular_value_counts=(),
            distractor_correct_value_counts=(),
            distractor_display_value_counts=(),
        )

    file_problem_count, file_distractor_count = parse_problem_counts(spec.activity_path)
    counts = CountSummary(
        file_problem_count=file_problem_count,
        file_distractor_count=file_distractor_count,
        regular_space_count=7,
        distractor_correct_count=5,
        distractor_display_count=5,
    )

    if spec.expected_problem_count is not None and file_problem_count != spec.expected_problem_count:
        errors.append(
            f"Expected {spec.expected_problem_count} <problem> tags, found {file_problem_count}."
        )
    if spec.expected_distractor_count is not None and file_distractor_count != spec.expected_distractor_count:
        errors.append(
            f"Expected {spec.expected_distractor_count} distractors, found {file_distractor_count}."
        )

    regular_value_sets = {label: set() for label in RADICAL_REGULAR_LABELS}
    distractor_display_sets = {
        label: {value} for label, value in RADICAL_DISTRACTOR_DISPLAYS.items()
    }
    distractor_overlap_examples: list[tuple[str, int, str]] = []
    unchecked_root_examples: dict[str, list[tuple[str, int, dict[str, int]]]] = defaultdict(list)

    for regular_display in iter_radical_solution_assignments():
        for label, value in regular_display.items():
            regular_value_sets[label].add(value)

        values = tuple(regular_display.values())
        if len(set(values)) != len(values) and not any(
            error.startswith("Regular displayed answers collide") for error in errors
        ):
            errors.append("Regular displayed answers collide for at least one global solution assignment.")

        all_displayed = dict(regular_display)
        for label, value in RADICAL_DISTRACTOR_DISPLAYS.items():
            if value in regular_display.values() and len(distractor_overlap_examples) < 5:
                matching_regular = next(
                    regular_label
                    for regular_label, regular_value in regular_display.items()
                    if regular_value == value
                )
                distractor_overlap_examples.append((label, value, matching_regular))
            all_displayed[label] = value

        for k4 in range(8, 10):
            for a4 in range(4, 6):
                extra_root = regular_display["problem 4"] + 2 * k4 + a4
                hit_labels = [
                    label for label, value in all_displayed.items() if value == extra_root
                ]
                if hit_labels and len(unchecked_root_examples["problem 4"]) < 5:
                    unchecked_root_examples["problem 4"].append(
                        (
                            ", ".join(hit_labels),
                            extra_root,
                            {
                                "problem 4": regular_display["problem 4"],
                                "problem 5": regular_display["problem 5"],
                                "problem 6": regular_display["problem 6"],
                                "problem 7": regular_display["problem 7"],
                                "k4": k4,
                                "a4": a4,
                            },
                        )
                    )

        extra_root = regular_display["problem 6"] - 8
        hit_labels = [label for label, value in all_displayed.items() if value == extra_root]
        if hit_labels and len(unchecked_root_examples["problem 6"]) < 5:
            unchecked_root_examples["problem 6"].append(
                (
                    ", ".join(hit_labels),
                    extra_root,
                    {
                        "problem 6": regular_display["problem 6"],
                        "problem 7": regular_display["problem 7"],
                    },
                )
            )

    if distractor_overlap_examples:
        label, value, matching_regular = distractor_overlap_examples[0]
        errors.append(
            f"A distractor displayed answer overlaps a regular answer. Example: {label} uses {value}, which matches {matching_regular}."
        )

    if unchecked_root_examples["problem 4"]:
        hit_labels, extra_root, example = unchecked_root_examples["problem 4"][0]
        errors.append(
            "Problem 4 has an unchecked extra root that lands on a displayed answer. "
            f"Example: problem 4 answer {example['problem 4']} with k4={example['k4']} and a4={example['a4']} "
            f"produces extra root {extra_root}, which matches {hit_labels}."
        )

    if unchecked_root_examples["problem 6"]:
        hit_labels, extra_root, example = unchecked_root_examples["problem 6"][0]
        errors.append(
            "Problem 6 has an unchecked extra root that lands on a displayed answer. "
            f"Example: problem 6 answer {example['problem 6']} with problem 7 answer {example['problem 7']} "
            f"produces extra root {extra_root}, which matches {hit_labels}."
        )

    regular_value_counts = tuple(
        (label, len(regular_value_sets[label])) for label in RADICAL_REGULAR_LABELS
    )
    distractor_correct_value_counts = tuple(
        (label.replace("displayed", "correct"), 0)
        for label in RADICAL_DISTRACTOR_DISPLAYS
    )
    distractor_display_value_counts = tuple(
        (label, len(distractor_display_sets[label]))
        for label in RADICAL_DISTRACTOR_DISPLAYS
    )

    return ValidationResult(
        spec=spec,
        counts=counts,
        errors=tuple(errors),
        overlap_issues=(),
        regular_value_counts=regular_value_counts,
        distractor_correct_value_counts=distractor_correct_value_counts,
        distractor_display_value_counts=distractor_display_value_counts,
    )


def build_complex_numbers_spec() -> ActivitySpec:
    activity_path = INTALG_ROOT / "Radical Functions/(Salty Pretzel) - Complex Numbers.doenet"

    regular_spaces = [
        constant_space("problem 1", (1, 0), "powers of i to 1"),
        constant_space("problem 2", (0, 1), "powers of i to i"),
        constant_space("problem 3", (-1, 0), "powers of i to -1"),
        constant_space("problem 4", (0, -1), "powers of i to -i"),
        mapped_space(
            "problem 5",
            [range(-16, -10), range(2, 7)],
            lambda real, imag: (real, imag),
            "sum of a real and a complex number",
        ),
        mapped_space(
            "problem 6",
            [range(-9, -3), range(8, 13)],
            lambda real, imag: (real, imag),
            "sum of two complex numbers",
        ),
        mapped_space(
            "problem 8",
            [range(3, 9), range(2, 7)],
            lambda real, imag_mag: (real, -imag_mag),
            "difference with real minus complex",
        ),
        mapped_space(
            "problem 9",
            [range(10, 16), range(7, 12)],
            lambda real, imag_mag: (real, -imag_mag),
            "difference of two complex numbers",
        ),
        mapped_space(
            "problem 11",
            [range(4, 7), range(4, 7), range(5, 8)],
            lambda factor, real_inside, imag_inside: (
                factor * real_inside,
                factor * imag_inside,
            ),
            "scalar times complex number",
        ),
        mapped_space(
            "problem 12",
            [range(10, 15), range(1, 4)],
            lambda u, v: (u - v, u + v),
            "product with 1+i",
        ),
        mapped_space(
            "problem 13",
            [range(-12, -7), range(7, 11)],
            lambda half_real, half_imag: (2 * half_real, 2 * half_imag),
            "triple product with (1+i)(1-i)",
        ),
        mapped_space(
            "problem 14",
            [range(2, 5), range(5, 8)],
            lambda a, b_abs: (a * a - b_abs * b_abs, -2 * a * b_abs),
            "square of a complex number",
        ),
        mapped_space(
            "problem 15",
            [range(3, 5), range(3, 5)],
            lambda a, b: (
                a**3 - 3 * a * b * b,
                3 * a * a * b - b**3,
            ),
            "cube of a complex number",
        ),
        mapped_space(
            "problem 16",
            [range(2, 7)],
            lambda k: (0, -k),
            "quotient of a real by bi",
        ),
        mapped_space(
            "problem 17",
            [range(5, 8), range(6, 9), range(2, 4)],
            lambda b, c, k: (k * b, -k * c),
            "quotient of a real by b+ci",
        ),
        mapped_space(
            "problem 18",
            [range(5, 9), range(18, 25)],
            lambda real_mag, imag: (-real_mag, imag),
            "quotient of a+bi by 1+i",
        ),
        mapped_space(
            "problem 19",
            [range(22, 29), range(13, 20)],
            lambda real, imag_mag: (real, -imag_mag),
            "quotient of a+bi by ci",
        ),
    ]

    distractor_correct_spaces = [
        mapped_space(
            "problem 7 correct",
            [range(18, 25), range(3, 8)],
            lambda real, imag: (real, imag),
            "correct answer for distractor 7",
        ),
        mapped_space(
            "problem 10 correct",
            [range(18, 25), range(3, 8)],
            lambda real_mag, imag_mag: (-real_mag, -imag_mag),
            "correct answer for distractor 10",
        ),
        mapped_space(
            "problem 20 correct",
            [range(3, 6), range(7, 10), range(2, 4)],
            lambda factor, real_inside, imag_inside: (
                factor * real_inside,
                factor * imag_inside,
            ),
            "correct answer for distractor 20",
        ),
    ]

    distractor_display_spaces = [
        mapped_space(
            "problem 7 displayed",
            [range(18, 25), range(3, 8)],
            lambda real, imag: (real + 50, imag),
            "displayed distractor answer for problem 7",
        ),
        mapped_space(
            "problem 10 displayed",
            [range(18, 25), range(3, 8)],
            lambda real_mag, imag_mag: (-real_mag, -(imag_mag + 60)),
            "displayed distractor answer for problem 10",
        ),
        mapped_space(
            "problem 20 displayed",
            [range(3, 6), range(7, 10), range(2, 4)],
            lambda factor, real_inside, imag_inside: (
                factor * real_inside + 80,
                factor * imag_inside + 40,
            ),
            "displayed distractor answer for problem 20",
        ),
    ]

    return ActivitySpec(
        name="complex_numbers",
        activity_path=activity_path,
        regular_spaces=regular_spaces,
        distractor_correct_spaces=distractor_correct_spaces,
        distractor_display_spaces=distractor_display_spaces,
        expected_problem_count=20,
        expected_distractor_count=3,
        answer_formatter=format_complex,
    )


def build_radical_equations_spec() -> ActivitySpec:
    activity_path = INTALG_ROOT / "Radical Functions/Radical Equations.doenet"

    return ActivitySpec(
        name="radical_equations",
        activity_path=activity_path,
        regular_spaces=(),
        distractor_correct_spaces=(),
        distractor_display_spaces=(),
        expected_problem_count=12,
        expected_distractor_count=5,
        answer_formatter=format_scalar,
        custom_validator=validate_radical_equations,
    )


def build_point_slope_form_spec() -> ActivitySpec:
    activity_path = INTALG_ROOT / "Linear Functions/(Salty Pretzel) - Point Slope Form.doenet"

    return ActivitySpec(
        name="point_slope_form",
        activity_path=activity_path,
        regular_spaces=(),
        distractor_correct_spaces=(),
        distractor_display_spaces=(),
        expected_problem_count=10,
        expected_distractor_count=4,
        answer_formatter=format_point_slope,
        custom_validator=validate_point_slope_form,
    )


def build_linear_inequalities_spec() -> ActivitySpec:
    activity_path = INTALG_ROOT / "Linear Functions/(Salty Pretzel) - Linear Inequalities in One Variable.doenet"

    return ActivitySpec(
        name="linear_inequalities",
        activity_path=activity_path,
        regular_spaces=(),
        distractor_correct_spaces=(),
        distractor_display_spaces=(),
        expected_problem_count=8,
        expected_distractor_count=1,
        answer_formatter=format_inequality,
        custom_validator=validate_linear_inequalities,
    )


def build_slope_intercept_form_spec() -> ActivitySpec:
    activity_path = INTALG_ROOT / "Linear Functions/(Salty Pretzel) - Slope Intercept Form.doenet"

    return ActivitySpec(
        name="slope_intercept_form",
        activity_path=activity_path,
        regular_spaces=(),
        distractor_correct_spaces=(),
        distractor_display_spaces=(),
        expected_problem_count=12,
        expected_distractor_count=2,
        answer_formatter=format_slope_intercept,
        custom_validator=validate_slope_intercept_form,
    )


def build_parallel_perpendicular_spec() -> ActivitySpec:
    activity_path = INTALG_ROOT / "Linear Functions/(Salty Pretzel) - Parallel and Perpendicular Lines.doenet"

    return ActivitySpec(
        name="parallel_perpendicular_lines",
        activity_path=activity_path,
        regular_spaces=(),
        distractor_correct_spaces=(),
        distractor_display_spaces=(),
        expected_problem_count=16,
        expected_distractor_count=6,
        answer_formatter=format_slope_intercept,
        custom_validator=validate_parallel_perpendicular_lines,
    )


def build_tutorial_circuits_and_pretzels_spec() -> ActivitySpec:
    activity_path = INTALG_ROOT / "Linear Functions/(Tutorial) - Circuits, Pretzels and Salty Pretzels.doenet"

    return ActivitySpec(
        name="tutorial_circuits_pretzels",
        activity_path=activity_path,
        regular_spaces=(),
        distractor_correct_spaces=(),
        distractor_display_spaces=(),
        expected_problem_count=16,
        expected_distractor_count=2,
        answer_formatter=format_tutorial_scalar,
        custom_validator=validate_tutorial_circuits_and_pretzels,
    )


REGISTERED_SPECS = {
    spec.name: spec
    for spec in [
        build_complex_numbers_spec(),
        build_linear_inequalities_spec(),
        build_parallel_perpendicular_spec(),
        build_radical_equations_spec(),
        build_point_slope_form_spec(),
        build_slope_intercept_form_spec(),
        build_tutorial_circuits_and_pretzels_spec(),
    ]
}