"""Declared-placeholder checks for HTML document templates.

Jinja is used only as a parser. Rendering and I/O stay outside this package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, TemplateSyntaxError, nodes

VERSION = "1.0.0"
REFERENCE = (
    "Document templates declare a placeholder map and reject any reference "
    "that is not in that map (architecture §21 and §25.12)."
)


@dataclass(frozen=True, slots=True)
class PlaceholderIssue:
    """Stable reason for a template that must not be saved."""

    reason: str
    name: str | None = None
    line: int | None = None


def validate_placeholders(
    sources: tuple[str, ...],
    declared: set[str],
) -> PlaceholderIssue | None:
    """Return the first problem, or None when every reference is declared."""

    referenced: set[str] = set()
    for source in sources:
        try:
            found = referenced_paths(source)
        except TemplateSyntaxError as exc:
            return PlaceholderIssue(reason="syntax", line=exc.lineno)
        if found is None:
            return PlaceholderIssue(reason="unsupported")
        referenced |= found
    undeclared = sorted(referenced - declared)
    if undeclared:
        return PlaceholderIssue(reason="undeclared", name=undeclared[0])
    return None


def referenced_paths(source: str) -> set[str] | None:
    """
    Placeholder paths used by a template.

    None means a lookup the validator cannot prove is declared (dynamic item).
    """

    environment = Environment()
    parsed = environment.parse(source)
    inner_ids = _inner_node_ids(parsed)
    loop_names = _loop_target_names(parsed)
    found: set[str] = set()
    for node in parsed.find_all((nodes.Getattr, nodes.Getitem)):
        if id(node) in inner_ids:
            continue
        path = _path(node)
        if path is None:
            return None
        found.add(path)
    for node in parsed.find_all(nodes.Name):
        if id(node) in inner_ids or node.ctx != "load":
            continue
        if node.name in loop_names:
            continue
        found.add(node.name)
    return found


def _inner_node_ids(parsed: nodes.Template) -> set[int]:
    inner: set[int] = set()
    for node in parsed.find_all((nodes.Getattr, nodes.Getitem)):
        inner.add(id(node.node))
    return inner


def _loop_target_names(parsed: nodes.Template) -> set[str]:
    names: set[str] = set()
    for loop in parsed.find_all(nodes.For):
        names |= _target_names(loop.target)
    return names


def _target_names(target: nodes.Node) -> set[str]:
    if isinstance(target, nodes.Name):
        return {target.name}
    if isinstance(target, nodes.Tuple):
        names: set[str] = set()
        for item in target.items:
            names |= _target_names(item)
        return names
    return set()


def _path(node: nodes.Node) -> str | None:
    parts: list[str] = []
    current: nodes.Node = node
    while True:
        if isinstance(current, nodes.Getattr):
            parts.append(current.attr)
            current = current.node
            continue
        if (
            isinstance(current, nodes.Getitem)
            and isinstance(current.arg, nodes.Const)
            and isinstance(current.arg.value, str)
        ):
            parts.append(current.arg.value)
            current = current.node
            continue
        break
    if isinstance(current, nodes.Name):
        parts.append(current.name)
        return ".".join(reversed(parts))
    return None


def lookup_path(data: dict[str, Any], path: str) -> Any:
    """Walk a dotted path. Missing segments return None."""

    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def missing_required(
    placeholders: dict[str, dict[str, Any]],
    data: dict[str, Any],
) -> list[str]:
    """Paths marked required whose value is absent. Empty lists count as present."""

    missing: list[str] = []
    for path, spec in placeholders.items():
        if not bool(spec.get("required", True)):
            continue
        if lookup_path(data, path) is None:
            missing.append(path)
    return missing
