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
    heavy: bool = False


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
    heavy: bool = False


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
    drawer_gap: int
    eye_level: int


@dataclass
class SolverConfig:
    time_limit: int = 60
    num_workers: int = 8
    symmetry_level: int = 2

    # Objective weights
    cabinet_weight: int = 1000000
    bin_weight: int = 10000
    family_weight: int = 6000
    span_weight: int = 0
    visibility_weight: int = 100
    heavy_weight: int = 100
    family_cabinet_span_weight: int = 1
    family_height_span_weight: int = 1

    # Constraint variant
    use_global_nooverlap: bool = True
