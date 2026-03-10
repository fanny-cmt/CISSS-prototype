from ortools.sat.python import cp_model

from src.types import Item, BinType, Geometry, PlacedItem, BinSolution, Solution, SolverConfig
from src.model import build_model


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
) -> Solution:
    if config is None:
        config = SolverConfig()

    print(f"[1/5] Preprocessing {len(items)} items...")
    original_ids, sorted_items = _preprocess_items(items)
    _validate_items(sorted_items, bin_types)

    print("[2/5] Building model (variables, constraints, objective)...")
    model, variables = build_model(sorted_items, families, bin_types, geometry, config)

    print(f"[3/5] Solving (time_limit={config.time_limit}s, workers={config.num_workers})...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config.time_limit
    solver.parameters.num_search_workers = config.num_workers
    solver.parameters.symmetry_level = config.symmetry_level

    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"No solution found (status: {solver.status_name(status)})")
        return Solution(status=solver.status_name(status), objective=None, num_bins=None, num_cabinets=None, bins=[])

    print(f"[4/5] Extracting solution (status: {solver.status_name(status)})...")
    bins = _extract_solution(solver, sorted_items, original_ids, variables)

    num_bins = solver.value(variables["num_bins"])
    num_cabinets = solver.value(variables["num_cabinets"])
    print(f"[5/5] Done! {num_bins} bins, {num_cabinets} cabinets.")
    return Solution(
        status=solver.status_name(status),
        objective=solver.objective_value,
        num_bins=num_bins,
        num_cabinets=num_cabinets,
        bins=bins,
    )
