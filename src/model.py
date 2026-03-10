from dataclasses import dataclass, field


@dataclass
class Item:
    id: int
    family: int
    w: int
    d: int


@dataclass
class PlacedItem:
    item: int
    family: int
    w: int
    d: int
    x: int
    y: int


@dataclass
class BinSolution:
    bin_id: int
    type: int
    W: int
    D: int
    items: list[PlacedItem] = field(default_factory=list)


@dataclass
class Solution:
    status: str
    objective: int | None
    bins: list[BinSolution]


@dataclass
class SolverConfig:
    separator: int = 1
    time_limit: int = 60
    num_workers: int = 8
    symmetry_level: int = 2

    # Objective weights
    bin_weight: int = 1000
    family_weight: int = 10
    span_weight: int = 1
