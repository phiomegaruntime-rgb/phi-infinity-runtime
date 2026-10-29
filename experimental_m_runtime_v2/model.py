"""Closed fragment graph model for the independent experimental runtime v2."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class FragmentRef:
    """Opaque semantic identity; semantic code consumes only this type."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str or not self.value:
            raise TypeError("FragmentRef requires a non-empty host identity.")

    def __str__(self) -> str:
        return self.value


KIND_FRAGMENT = FragmentRef("kind:fragment")
KIND_ATOM = FragmentRef("kind:atom")
KIND_INFINITO = FragmentRef("kind:infinito")
KIND_AUTHORITY = FragmentRef("kind:authority")
KIND_FREEZE = FragmentRef("kind:freeze")
KIND_MACHINE = FragmentRef("kind:machine")
KIND_TARGET = FragmentRef("kind:target")
KIND_RECEIPT = FragmentRef("kind:receipt")
KIND_OUTPUT = FragmentRef("kind:output")
KIND_CLAIM = FragmentRef("kind:claim")
KIND_GENEALOGY = FragmentRef("kind:genealogy")
KIND_DEPENDENCY = FragmentRef("kind:dependency")

ADMISSION_ALLOW = FragmentRef("decision:ALLOW")
ADMISSION_BLOCK = FragmentRef("decision:BLOCK")
ADMISSION_REOPEN = FragmentRef("decision:REOPEN")


@dataclass(frozen=True, slots=True)
class FragmentNode:
    """A node whose complete semantic content is made of fragment references."""

    ref: FragmentRef
    kind: FragmentRef
    edges: tuple[FragmentRef, ...]

    def __post_init__(self) -> None:
        if type(self.ref) is not FragmentRef or type(self.kind) is not FragmentRef:
            raise TypeError("FragmentNode identity and kind must be FragmentRef.")
        if type(self.edges) is not tuple:
            raise TypeError("FragmentNode edges must be a tuple of FragmentRef.")
        if any(type(edge) is not FragmentRef for edge in self.edges):
            raise TypeError("FragmentNode edges must contain only FragmentRef.")
        if len(self.edges) != len(set(self.edges)):
            raise ValueError("FragmentNode edges must be identity-unique.")


@dataclass(frozen=True, slots=True)
class ClosureReport:
    is_closed: bool
    reason: FragmentRef


@dataclass(frozen=True, slots=True)
class FragmentGraph:
    """Immutable execution snapshot with Infinito as its root fragment."""

    infinito: FragmentRef
    authority: FragmentRef
    target: FragmentRef
    machine: FragmentRef
    path: tuple[FragmentRef, ...]
    nodes: Mapping[FragmentRef, FragmentNode]

    def __post_init__(self) -> None:
        refs = (self.infinito, self.authority, self.target, self.machine)
        if any(type(item) is not FragmentRef for item in refs):
            raise TypeError("Graph anchors must be FragmentRef.")
        if type(self.path) is not tuple or not self.path:
            raise TypeError("A graph requires a non-empty FragmentRef path.")
        if any(type(item) is not FragmentRef for item in self.path):
            raise TypeError("Graph path must contain only FragmentRef.")
        if len(self.path) != len(set(self.path)):
            raise ValueError("Graph path identities must be unique.")
        if not isinstance(self.nodes, Mapping):
            raise TypeError("Graph nodes must be a mapping of FragmentRef values.")
        copied = dict(self.nodes)
        if any(type(key) is not FragmentRef for key in copied):
            raise TypeError("Graph node keys must be FragmentRef.")
        if any(type(value) is not FragmentNode for value in copied.values()):
            raise TypeError("Graph node values must be FragmentNode.")
        if any(key != value.ref for key, value in copied.items()):
            raise ValueError("Graph node keys must match node identities.")
        object.__setattr__(self, "path", tuple(self.path))
        object.__setattr__(self, "nodes", MappingProxyType(copied))

    def validate_closed(self) -> ClosureReport:
        """Check total reference closure and reachability from Infinito."""

        if self.infinito not in self.nodes:
            return ClosureReport(False, FragmentRef("reason:missing-infinito-root"))
        root = self.nodes[self.infinito]
        if root.kind != KIND_INFINITO:
            return ClosureReport(False, FragmentRef("reason:invalid-infinito-root"))

        visited: set[FragmentRef] = set()
        pending = [self.infinito]
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            node = self.nodes.get(current)
            if node is None:
                return ClosureReport(False, FragmentRef("reason:dangling-reference"))
            visited.add(current)
            references = (node.kind,) + node.edges
            for reference in references:
                if type(reference) is not FragmentRef:
                    return ClosureReport(False, FragmentRef("reason:raw-reference"))
                if reference not in self.nodes:
                    return ClosureReport(False, FragmentRef("reason:dangling-reference"))
                if reference not in visited:
                    pending.append(reference)

        if visited != set(self.nodes):
            return ClosureReport(False, FragmentRef("reason:unreachable-fragment"))
        return ClosureReport(True, FragmentRef("reason:closed-fragment-graph"))


@dataclass(frozen=True, slots=True)
class AdmissionResult:
    """Only fragment references cross the semantic result boundary."""

    decision: FragmentRef
    reason: FragmentRef
    error: FragmentRef
    output: FragmentRef
    receipt: FragmentRef
    graph: FragmentGraph