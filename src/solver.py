import time

from ortools.sat.python import cp_model

from src.types import Item, BinType, Geometry, PlacedItem, BinSolution, Solution, SolverConfig
from src.model import build_model
from src.heuristic import compute_greedy_max_bins


class _ProgressCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        super().__init__()
        self._start_time = time.time()
        self._solution_count = 0

    def on_solution_callback(self):
        self._solution_count += 1
        elapsed = time.time() - self._start_time
        obj = self.objective_value
        bound = self.best_objective_bound
        gap = abs(obj - bound) / max(abs(obj), 1e-9) * 100
        print(f"      [{elapsed:6.1f}s] Solution #{self._solution_count}: obj={obj:.0f} | bound={bound:.0f} | gap={gap:.2f}%")


def _preprocess_items(items: list[Item]) -> tuple[list[int], list[Item]]:
    indexed_items = list(enumerate(items))
    indexed_items.sort(key=lambda p: (p[1].family, -max(v.w * v.d for v in p[1].variants)))

    original_ids = [idx for idx, _ in indexed_items]
    sorted_items = [item for _, item in indexed_items]
    return original_ids, sorted_items


def _validate_items(items: list[Item], bin_types: list[BinType]) -> None:
    for item in items:
        fits = any(
            v.w <= bt.W and v.d <= bt.D
            for v in item.variants
            for bt in bin_types
        )
        if not fits:
            raise ValueError(f"Objet {item.id} impossible à placer: aucune variante ne rentre dans aucun bac")


def _extract_solution(solver: cp_model.CpSolver, items: list[Item], original_ids: list[int], variables: dict) -> list[BinSolution]:
    bin_of = variables["bin_of"]
    x = variables["x"]
    y = variables["y"]
    bin_type = variables["bin_type"]
    W_of_bin = variables["W_of_bin"]
    D_of_bin = variables["D_of_bin"]
    H_of_bin = variables["H_of_bin"]
    occupied_height_of_bin = variables["occupied_height_of_bin"]
    Z_of_bin = variables["Z_of_bin"]
    cabinet_of_bin = variables["cabinet_of_bin"]
    variant_of = variables["variant_of"]
    eff_w = variables["eff_w"]
    eff_d = variables["eff_d"]
    eff_h = variables["eff_h"]

    bins: dict[int, BinSolution] = {}
    for i, item in enumerate(items):
        k = solver.value(bin_of[i])
        if k not in bins:
            t = solver.value(bin_type[k])
            bins[k] = BinSolution(
                bin_id=k,
                type=t,
                W=solver.value(W_of_bin[k]),
                D=solver.value(D_of_bin[k]),
                H=solver.value(H_of_bin[k]),
                occupied_H=solver.value(occupied_height_of_bin[k]),
                cabinet=solver.value(cabinet_of_bin[k]),
                Z=solver.value(Z_of_bin[k]),
            )
        bins[k].items.append(PlacedItem(
            item=original_ids[i],
            family=item.family,
            weight=item.weight,
            variant=solver.value(variant_of[i]),
            w=solver.value(eff_w[i]),
            d=solver.value(eff_d[i]),
            h=solver.value(eff_h[i]),
            x=solver.value(x[i]),
            y=solver.value(y[i]),
        ))

    return [bins[k] for k in sorted(bins)]


def solve_2d_bins_fast(
    items: list[Item],
    families,
    bin_types: list[BinType],
    geometry: Geometry,
    config: SolverConfig | None = None,
    visible_families: list[int] | None = None,
) -> Solution:
    if config is None:
        config = SolverConfig()

    print(f"[1/6] Preprocessing {len(items)} items...")
    original_ids, sorted_items = _preprocess_items(items)
    _validate_items(sorted_items, bin_types)

    print("[2/6] Computing greedy upper bound...")
    max_bins, max_cabinets = compute_greedy_max_bins(sorted_items, bin_types, geometry)
    print(f"      Greedy bound: {max_bins} bins, {max_cabinets} cabinets (K={max_bins} candidate slots)")

    print("[3/6] Building model (variables, constraints, objective)...")
    model, variables = build_model(sorted_items, families, bin_types, geometry, config, visible_families=visible_families, max_bins=max_bins, max_cabinets=max_cabinets)

    print(f"[4/6] Solving (time_limit={config.time_limit}s, workers={config.num_workers})...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config.time_limit
    solver.parameters.num_search_workers = config.num_workers
    solver.parameters.symmetry_level = config.symmetry_level
    solver.log_search_progress = True

    callback = _ProgressCallback()
    status = solver.solve(model, callback)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"No solution found (status: {solver.status_name(status)})")
        return Solution(status=solver.status_name(status), objective=None, num_bins=None, num_cabinets=None, bins=[])

    print(f"[5/6] Extracting solution (status: {solver.status_name(status)})...")
    bins = _extract_solution(solver, sorted_items, original_ids, variables)

    num_bins = solver.value(variables["num_bins"])
    num_cabinets = solver.value(variables["num_cabinets"])

    obj = solver.objective_value
    bound = solver.best_objective_bound
    gap = abs(obj - bound) / max(abs(obj), 1e-9) * 100
    print(f"[6/6] Done! {num_bins} bins, {num_cabinets} cabinets.")
    print(f"      Objective: {obj:.0f} | Bound: {bound:.0f} | Gap: {gap:.2f}%")
    return Solution(
        status=solver.status_name(status),
        objective=solver.objective_value,
        num_bins=num_bins,
        num_cabinets=num_cabinets,
        bins=bins,
    )
