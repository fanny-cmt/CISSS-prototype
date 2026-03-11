"""
Greedy upper-bound heuristic for bin and cabinet counts.

Uses a shelf-based 2D packing: items are placed left-to-right in rows (shelves).
When an item doesn't fit on the current shelf, a new shelf is opened.
When no shelf fits in the current bin, a new bin is opened.

The heuristic is conservative: it may overestimate the number of bins,
but it guarantees a feasible packing exists with at most that many bins.
"""

from src.types import Item, BinType, Geometry


class _Shelf:
    """A horizontal row inside a bin, at a given y offset."""

    __slots__ = ("y", "shelf_h", "cursor_x", "W")

    def __init__(self, y: int, W: int):
        self.y = y
        self.shelf_h = 0
        self.cursor_x = 0
        self.W = W

    def fits(self, w: int, d: int) -> bool:
        return self.cursor_x + w <= self.W and (self.shelf_h == 0 or d <= self.shelf_h)

    def place(self, w: int, d: int) -> None:
        self.cursor_x += w
        self.shelf_h = max(self.shelf_h, d)


class _OpenBin:
    """A bin being filled by the greedy heuristic."""

    __slots__ = ("bt", "shelves", "current_weight", "max_h_item")

    def __init__(self, bt: BinType):
        self.bt = bt
        self.shelves: list[_Shelf] = [_Shelf(0, bt.W)]
        self.current_weight = 0
        self.max_h_item = 0

    def try_place(self, w: int, d: int, h: int, weight: int) -> bool:
        """Try to place an item (w x d, height h, weight) in this bin."""
        # Height compatibility: 10 * h <= 13 * H
        if 10 * h > 13 * self.bt.H:
            return False
        # Weight check
        if self.current_weight + weight > self.bt.max_weight:
            return False

        # Try existing shelves
        for shelf in self.shelves:
            if shelf.fits(w, d):
                shelf.place(w, d)
                self.current_weight += weight
                self.max_h_item = max(self.max_h_item, h)
                return True

        # Open a new shelf
        last = self.shelves[-1]
        new_y = last.y + last.shelf_h
        if new_y + d <= self.bt.D:
            shelf = _Shelf(new_y, self.bt.W)
            shelf.place(w, d)
            self.shelves.append(shelf)
            self.current_weight += weight
            self.max_h_item = max(self.max_h_item, h)
            return True

        return False

    @property
    def occupied_height(self) -> int:
        return max(self.bt.H, self.max_h_item)


def _best_variant_for_bin(item: Item, bt: BinType) -> tuple[int, int, int] | None:
    """Pick the variant that fits in bt and has the smallest area (w*d)."""
    best = None
    for v in item.variants:
        if v.w <= bt.W and v.d <= bt.D and 10 * v.h <= 13 * bt.H:
            area = v.w * v.d
            if best is None or area < best[0]:
                best = (area, v.w, v.d, v.h)
    return (best[1], best[2], best[3]) if best else None


def compute_greedy_max_bins(
    items: list[Item],
    bin_types: list[BinType],
    geometry: Geometry,
) -> tuple[int, int]:
    """
    Conservative greedy heuristic: one family per bin.

    Returns (max_bins, max_cabinets).

    Strategy:
    - Group items by family.
    - For each family, pack its items (sorted by decreasing area) into
      dedicated bins using shelf-based 2D placement.
    - A family may use multiple bins if items don't fit in one.
    - Families never share bins — this is intentionally conservative
      to guarantee a safe upper bound.
    - Bin types are tried from largest H to smallest (conservative).
    - Cabinets are estimated by greedily stacking bin occupied heights.
    """
    # Sort bin types by H descending (largest first = most conservative)
    sorted_bt = sorted(bin_types, key=lambda bt: bt.H, reverse=True)

    # Group items by family
    families: dict[int, list[Item]] = {}
    for item in items:
        families.setdefault(item.family, []).append(item)

    open_bins: list[_OpenBin] = []

    for fam_id in sorted(families):
        # Sort family items by decreasing max variant area
        fam_items = sorted(
            families[fam_id],
            key=lambda it: -max(v.w * v.d for v in it.variants),
        )

        # Bins dedicated to this family
        fam_bins: list[_OpenBin] = []

        for item in fam_items:
            placed = False

            # Try existing bins for this family only
            for obin in fam_bins:
                variant = _best_variant_for_bin(item, obin.bt)
                if variant is None:
                    continue
                w, d, h = variant
                if obin.try_place(w, d, h, item.weight):
                    placed = True
                    break

            if not placed:
                # Open a new bin — try largest compatible bin type first
                for bt in sorted_bt:
                    variant = _best_variant_for_bin(item, bt)
                    if variant is None:
                        continue
                    new_bin = _OpenBin(bt)
                    w, d, h = variant
                    if new_bin.try_place(w, d, h, item.weight):
                        fam_bins.append(new_bin)
                        placed = True
                        break

                if not placed:
                    # Fallback: open a bin with the largest type
                    bt = sorted_bt[0]
                    new_bin = _OpenBin(bt)
                    for v in item.variants:
                        if v.w <= bt.W and v.d <= bt.D:
                            new_bin.try_place(v.w, v.d, v.h, item.weight)
                            placed = True
                            break
                    if placed:
                        fam_bins.append(new_bin)
                    else:
                        # Item cannot fit at all — still count a bin for safety
                        fam_bins.append(_OpenBin(sorted_bt[0]))

        open_bins.extend(fam_bins)

    max_bins = len(open_bins)

    # Greedy cabinet stacking
    max_cabinets = _greedy_cabinet_count(open_bins, geometry)

    return max_bins, max_cabinets


def _greedy_cabinet_count(open_bins: list[_OpenBin], geometry: Geometry) -> int:
    """
    Stack bins into cabinets greedily (first-fit decreasing on occupied height).

    Returns the number of cabinets needed.
    """
    cabinet_height = geometry.cabinet_height
    drawer_gap = geometry.drawer_gap

    # Sort bins by occupied height descending (FFD heuristic)
    heights = sorted(
        [obin.occupied_height for obin in open_bins],
        reverse=True,
    )

    # Each cabinet tracks remaining space
    cabinets: list[int] = []  # remaining height in each cabinet

    for h in heights:
        placed = False
        for i, remaining in enumerate(cabinets):
            if h + drawer_gap <= remaining:
                cabinets[i] = remaining - h - drawer_gap
                placed = True
                break
        if not placed:
            cabinets.append(cabinet_height - h - drawer_gap)

    return max(len(cabinets), 1)
