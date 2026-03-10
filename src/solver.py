from ortools.sat.python import cp_model

from src.types import Item, PlacedItem, BinSolution, Solution, SolverConfig
from src.model import build_model


def _preprocess_items(items: list[Item]) -> tuple[list[int], list[Item]]:
    indexed_items = list(enumerate(items))
    indexed_items.sort(key=lambda p: (p[1].family, -(p[1].w * p[1].d)))

    original_ids = [idx for idx, _ in indexed_items]
    sorted_items = [item for _, item in indexed_items]
    return original_ids, sorted_items


def _validate_items(items: list[Item], bin_types: list[tuple[int, int]]) -> None:
    for item in items:
        if all(item.w > W or item.d > D for W, D in bin_types):
            raise ValueError(f"Objet impossible à placer: {(item.w, item.d)}")


def _extract_solution(solver: cp_model.CpSolver, items: list[Item], original_ids: list[int], variables: dict) -> list[BinSolution]:
    bin_of = variables["bin_of"]
    x = variables["x"]
    y = variables["y"]
    bin_type = variables["bin_type"]
    W_of_bin = variables["W_of_bin"]
    D_of_bin = variables["D_of_bin"]

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
            )
        bins[k].items.append(PlacedItem(
            item=original_ids[i],
            family=item.family,
            w=item.w,
            d=item.d,
            x=solver.value(x[i]),
            y=solver.value(y[i]),
        ))

    return [bins[k] for k in sorted(bins)]


def solve_2d_bins_fast(
    items: list[Item],
    families,
    bin_types: list[tuple[int, int]],
    config: SolverConfig | None = None,
) -> Solution:
    if config is None:
        config = SolverConfig()

    print(f"[1/5] Preprocessing {len(items)} items...")
    original_ids, sorted_items = _preprocess_items(items)
    _validate_items(sorted_items, bin_types)

    print("[2/5] Building model (variables, constraints, objective)...")
    model, variables = build_model(sorted_items, families, bin_types, config)

    print(f"[3/5] Solving (time_limit={config.time_limit}s, workers={config.num_workers})...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config.time_limit
    solver.parameters.num_search_workers = config.num_workers
    solver.parameters.symmetry_level = config.symmetry_level

    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"No solution found (status: {solver.status_name(status)})")
        return Solution(status=solver.status_name(status), objective=None, bins=[])

    print(f"[4/5] Extracting solution (status: {solver.status_name(status)})...")
    bins = _extract_solution(solver, sorted_items, original_ids, variables)

    print(f"[5/5] Done! {len(bins)} bins used.")
    return Solution(
        status=solver.status_name(status),
        objective=solver.value(variables["num_bins"]),
        bins=bins,
    )
