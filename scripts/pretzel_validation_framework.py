from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Callable, Hashable, Iterable, Sequence


AnswerKey = Hashable
AnswerFormatter = Callable[[AnswerKey], str]


@dataclass(frozen=True)
class ProblemSpace:
    label: str
    values_factory: Callable[[], Iterable[AnswerKey]]
    description: str = ""

    def values(self) -> set[AnswerKey]:
        return set(self.values_factory())


@dataclass(frozen=True)
class ActivitySpec:
    name: str
    activity_path: Path
    regular_spaces: Sequence[ProblemSpace]
    distractor_correct_spaces: Sequence[ProblemSpace] = ()
    distractor_display_spaces: Sequence[ProblemSpace] = ()
    expected_problem_count: int | None = None
    expected_distractor_count: int | None = None
    answer_formatter: AnswerFormatter = repr
    custom_validator: Callable[["ActivitySpec"], "ValidationResult"] | None = None


@dataclass(frozen=True)
class OverlapIssue:
    category: str
    left_label: str
    right_label: str
    overlap_examples: tuple[AnswerKey, ...]

    @property
    def overlap_count(self) -> int:
        return len(self.overlap_examples)


@dataclass(frozen=True)
class CountSummary:
    file_problem_count: int
    file_distractor_count: int
    regular_space_count: int
    distractor_correct_count: int
    distractor_display_count: int


@dataclass(frozen=True)
class ValidationResult:
    spec: ActivitySpec
    counts: CountSummary
    errors: tuple[str, ...]
    overlap_issues: tuple[OverlapIssue, ...]
    regular_value_counts: tuple[tuple[str, int], ...]
    distractor_correct_value_counts: tuple[tuple[str, int], ...]
    distractor_display_value_counts: tuple[tuple[str, int], ...]

    @property
    def passed(self) -> bool:
        return not self.errors and not self.overlap_issues


@dataclass(frozen=True)
class PretzelInventoryEntry:
    activity_path: Path
    pretzel_count: int
    problem_count: int
    distractor_count: int
    modes: tuple[str, ...]


def validate_activity(spec: ActivitySpec) -> ValidationResult:
    if spec.custom_validator is not None:
        return spec.custom_validator(spec)

    errors: list[str] = []

    if not spec.activity_path.exists():
        errors.append(f"Activity file does not exist: {spec.activity_path}")
        counts = CountSummary(
            file_problem_count=0,
            file_distractor_count=0,
            regular_space_count=len(spec.regular_spaces),
            distractor_correct_count=len(spec.distractor_correct_spaces),
            distractor_display_count=len(spec.distractor_display_spaces),
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
        regular_space_count=len(spec.regular_spaces),
        distractor_correct_count=len(spec.distractor_correct_spaces),
        distractor_display_count=len(spec.distractor_display_spaces),
    )

    if spec.expected_problem_count is not None and file_problem_count != spec.expected_problem_count:
        errors.append(
            f"Expected {spec.expected_problem_count} <problem> tags, found {file_problem_count}."
        )
    if spec.expected_distractor_count is not None and file_distractor_count != spec.expected_distractor_count:
        errors.append(
            f"Expected {spec.expected_distractor_count} distractors, found {file_distractor_count}."
        )
    if len(spec.distractor_correct_spaces) != len(spec.distractor_display_spaces):
        errors.append(
            "Distractor correct-space count does not match distractor display-space count."
        )
    if file_problem_count and file_problem_count != (
        len(spec.regular_spaces) + len(spec.distractor_display_spaces)
    ):
        errors.append(
            "Declared validation spaces do not match the problem count in the activity file."
        )
    if file_distractor_count and file_distractor_count != len(spec.distractor_display_spaces):
        errors.append(
            "Declared distractor display spaces do not match the distractor count in the activity file."
        )

    regular_values = evaluate_spaces(spec.regular_spaces)
    distractor_correct_values = evaluate_spaces(spec.distractor_correct_spaces)
    distractor_display_values = evaluate_spaces(spec.distractor_display_spaces)

    overlap_issues: list[OverlapIssue] = []
    overlap_issues.extend(
        find_pairwise_overlaps(
            category="regular-vs-regular",
            evaluated_spaces=regular_values,
        )
    )
    overlap_issues.extend(
        find_cross_overlaps(
            category="distractor-correct-vs-regular",
            left_spaces=distractor_correct_values,
            right_spaces=regular_values,
        )
    )
    overlap_issues.extend(
        find_cross_overlaps(
            category="distractor-display-vs-regular",
            left_spaces=distractor_display_values,
            right_spaces=regular_values,
        )
    )
    overlap_issues.extend(
        find_cross_overlaps(
            category="distractor-display-vs-distractor-correct",
            left_spaces=distractor_display_values,
            right_spaces=distractor_correct_values,
        )
    )
    overlap_issues.extend(
        find_pairwise_overlaps(
            category="distractor-display-vs-distractor-display",
            evaluated_spaces=distractor_display_values,
        )
    )

    return ValidationResult(
        spec=spec,
        counts=counts,
        errors=tuple(errors),
        overlap_issues=tuple(overlap_issues),
        regular_value_counts=tuple((space.label, len(values)) for space, values in regular_values),
        distractor_correct_value_counts=tuple(
            (space.label, len(values)) for space, values in distractor_correct_values
        ),
        distractor_display_value_counts=tuple(
            (space.label, len(values)) for space, values in distractor_display_values
        ),
    )


def evaluate_spaces(
    spaces: Sequence[ProblemSpace],
) -> tuple[tuple[ProblemSpace, set[AnswerKey]], ...]:
    evaluated: list[tuple[ProblemSpace, set[AnswerKey]]] = []
    for space in spaces:
        values = space.values()
        evaluated.append((space, values))
    return tuple(evaluated)


def find_pairwise_overlaps(
    *,
    category: str,
    evaluated_spaces: Sequence[tuple[ProblemSpace, set[AnswerKey]]],
) -> list[OverlapIssue]:
    issues: list[OverlapIssue] = []
    for (left_space, left_values), (right_space, right_values) in combinations(
        evaluated_spaces, 2
    ):
        overlap = sorted(left_values & right_values, key=repr)
        if overlap:
            issues.append(
                OverlapIssue(
                    category=category,
                    left_label=left_space.label,
                    right_label=right_space.label,
                    overlap_examples=tuple(overlap[:10]),
                )
            )
    return issues


def find_cross_overlaps(
    *,
    category: str,
    left_spaces: Sequence[tuple[ProblemSpace, set[AnswerKey]]],
    right_spaces: Sequence[tuple[ProblemSpace, set[AnswerKey]]],
) -> list[OverlapIssue]:
    issues: list[OverlapIssue] = []
    for left_space, left_values in left_spaces:
        for right_space, right_values in right_spaces:
            overlap = sorted(left_values & right_values, key=repr)
            if overlap:
                issues.append(
                    OverlapIssue(
                        category=category,
                        left_label=left_space.label,
                        right_label=right_space.label,
                        overlap_examples=tuple(overlap[:10]),
                    )
                )
    return issues


def parse_problem_counts(activity_path: Path) -> tuple[int, int]:
    text = activity_path.read_text(encoding="utf-8", errors="replace")
    file_problem_count = len(re.findall(r"<problem\b", text))
    file_distractor_count = len(re.findall(r"<problem\b[^>]*\bisDistractor\b", text))
    return file_problem_count, file_distractor_count


def discover_pretzel_activities(root: Path) -> tuple[PretzelInventoryEntry, ...]:
    entries: list[PretzelInventoryEntry] = []
    for activity_path in sorted(root.rglob("*.doenet")):
        text = activity_path.read_text(encoding="utf-8", errors="replace")
        pretzel_tags = re.findall(r"<pretzel\b[^>]*>", text)
        if not pretzel_tags:
            continue
        modes = []
        for tag in pretzel_tags:
            match = re.search(r'\bmode\s*=\s*"([^"]+)"', tag)
            modes.append(match.group(1) if match else "default")
        problem_count = len(re.findall(r"<problem\b", text))
        distractor_count = len(re.findall(r"<problem\b[^>]*\bisDistractor\b", text))
        entries.append(
            PretzelInventoryEntry(
                activity_path=activity_path,
                pretzel_count=len(pretzel_tags),
                problem_count=problem_count,
                distractor_count=distractor_count,
                modes=tuple(modes),
            )
        )
    return tuple(entries)


def render_pretzel_inventory(
    entries: Sequence[PretzelInventoryEntry],
    *,
    root: Path,
    registered_specs_by_path: dict[Path, str],
) -> str:
    lines = ["Pretzel inventory:"]
    for entry in entries:
        resolved_path = entry.activity_path.resolve()
        registered_name = registered_specs_by_path.get(resolved_path)
        status = f"registered:{registered_name}" if registered_name else "unregistered"
        relative_path = entry.activity_path.relative_to(root).as_posix()
        lines.append(
            "- "
            f"[{status}] {relative_path} "
            f"(pretzels={entry.pretzel_count}, problems={entry.problem_count}, "
            f"distractors={entry.distractor_count}, modes={', '.join(entry.modes)})"
        )
    return "\n".join(lines)


def render_validation_result(result: ValidationResult, *, verbose: bool = False) -> str:
    lines = [
        f"Activity: {result.spec.name}",
        f"File: {result.spec.activity_path}",
        f"Status: {'PASS' if result.passed else 'FAIL'}",
        (
            "Counts: "
            f"file problems={result.counts.file_problem_count}, "
            f"file distractors={result.counts.file_distractor_count}, "
            f"regular spaces={result.counts.regular_space_count}, "
            f"distractor correct spaces={result.counts.distractor_correct_count}, "
            f"distractor display spaces={result.counts.distractor_display_count}"
        ),
    ]

    if verbose:
        lines.append("Regular reachable-answer counts:")
        for label, count in result.regular_value_counts:
            lines.append(f"- {label}: {count}")
        if result.distractor_correct_value_counts:
            lines.append("Distractor correct reachable-answer counts:")
            for label, count in result.distractor_correct_value_counts:
                lines.append(f"- {label}: {count}")
        if result.distractor_display_value_counts:
            lines.append("Distractor display reachable-answer counts:")
            for label, count in result.distractor_display_value_counts:
                lines.append(f"- {label}: {count}")

    if result.errors:
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"- {error}")

    if result.overlap_issues:
        lines.append("Overlap issues:")
        for issue in result.overlap_issues:
            examples = ", ".join(
                result.spec.answer_formatter(example)
                for example in issue.overlap_examples
            )
            lines.append(
                f"- {issue.category}: {issue.left_label} vs {issue.right_label} "
                f"({issue.overlap_count} overlap example(s): {examples})"
            )
    elif not result.errors:
        lines.append("No overlap issues found.")

    return "\n".join(lines)