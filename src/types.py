from dataclasses import dataclass, field


@dataclass(frozen=True)
class Variant:
    w: int
    d: int
    h: int


@dataclass(frozen=True)
class BinType:
    W: int
    D: int
    H: int
    max_weight: int


@dataclass(frozen=True)
class Item:
    id: int
    family: int
    weight: int
    variants: list[Variant]


@dataclass
class PlacedItem:
    item: int
    family: int
    weight: int
    variant: int
    w: int
    d: int
    h: int
    x: int
    y: int


@dataclass
class BinSolution:
    bin_id: int
    type: int
    W: int
    D: int
    H: int
    occupied_H: int
    cabinet: int
    Z: int
    items: list[PlacedItem] = field(default_factory=list)


@dataclass
class Solution:
    status: str
    objective: int | None
    num_bins: int | None
    num_cabinets: int | None
    bins: list[BinSolution]


@dataclass(frozen=True)
class Geometry:
    cabinet_height: int
    separator: int


@dataclass
class SolverConfig:
    time_limit: int = 60
    num_workers: int = 8
    symmetry_level: int = 2

    # Objective weights
    cabinet_weight: int = 100000
    bin_weight: int = 1000
    family_weight: int = 10
    span_weight: int = 1
