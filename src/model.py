from ortools.sat.python import cp_model

from src.types import Item, SolverConfig


def create_variables(model: cp_model.CpModel, items: list[Item], bin_types: list[tuple[int, int]], families):
    n = len(items)
    T = len(bin_types)

    max_W = max(W for W, _ in bin_types)
    max_D = max(D for _, D in bin_types)

    num_bins = model.new_int_var(1, n, "num_bins")

    bin_of = [model.new_int_var(0, i, f"bin_of[{i}]") for i in range(n)]
    x = [model.new_int_var(0, max_W, f"x[{i}]") for i in range(n)]
    y = [model.new_int_var(0, max_D, f"y[{i}]") for i in range(n)]

    bin_type = [model.new_int_var(0, T - 1, f"bin_type[{k}]") for k in range(n)]

    W_values = [W for W, _ in bin_types]
    D_values = [D for _, D in bin_types]

    W_of_bin = [model.new_int_var(min(W_values), max(W_values), f"W_of_bin[{k}]") for k in range(n)]
    D_of_bin = [model.new_int_var(min(D_values), max(D_values), f"D_of_bin[{k}]") for k in range(n)]

    for k in range(n):
        model.add_element(bin_type[k], W_values, W_of_bin[k])
        model.add_element(bin_type[k], D_values, D_of_bin[k])

    return {
        "num_bins": num_bins,
        "bin_of": bin_of,
        "x": x,
        "y": y,
        "bin_type": bin_type,
        "W_of_bin": W_of_bin,
        "D_of_bin": D_of_bin,
        "max_W": max_W,
        "max_D": max_D,
    }


def add_placement_constraints(model: cp_model.CpModel, items: list[Item], variables: dict):
    n = len(items)
    bin_of = variables["bin_of"]
    x = variables["x"]
    y = variables["y"]
    num_bins = variables["num_bins"]
    W_of_bin = variables["W_of_bin"]
    D_of_bin = variables["D_of_bin"]

    model.add(bin_of[0] == 0)
    for i in range(n):
        model.add(bin_of[i] < num_bins)

    is_in = {}
    for i, item in enumerate(items):
        for k in range(i + 1):
            is_in[i, k] = model.new_bool_var(f"is_in[{i},{k}]")
            model.add(bin_of[i] == k).only_enforce_if(is_in[i, k])
            model.add(bin_of[i] != k).only_enforce_if(is_in[i, k].Not())

            model.add(x[i] + item.w <= W_of_bin[k]).only_enforce_if(is_in[i, k])
            model.add(y[i] + item.d <= D_of_bin[k]).only_enforce_if(is_in[i, k])

    return is_in


def add_family_constraints(model: cp_model.CpModel, items: list[Item], families, is_in: dict, variables: dict):
    n = len(items)

    fam_in_bin = {}
    for f in families:
        for k in range(n):
            fam_in_bin[f, k] = model.new_bool_var(f"fam_{f}_in_bin_{k}")

    for i, item in enumerate(items):
        for k in range(i + 1):
            model.add_implication(is_in[i, k], fam_in_bin[item.family, k])

    for f in families:
        items_f = [i for i, item in enumerate(items) if item.family == f]

        for k in range(n):
            vars_in_bin = [is_in[i, k] for i in items_f if (i, k) in is_in]

            if vars_in_bin:
                model.add_max_equality(fam_in_bin[f, k], vars_in_bin)
            else:
                model.add(fam_in_bin[f, k] == 0)

    family_drawer_count = {}
    for f in families:
        family_drawer_count[f] = model.new_int_var(0, n, f"family_drawer_count_{f}")
        model.add(
            family_drawer_count[f] ==
            sum(fam_in_bin[f, k] for k in range(n))
        )

    return fam_in_bin, family_drawer_count


def add_spatial_span_constraints(model: cp_model.CpModel, items: list[Item], families, is_in: dict, fam_in_bin: dict, variables: dict):
    n = len(items)
    x = variables["x"]
    y = variables["y"]
    max_W = variables["max_W"]
    max_D = variables["max_D"]

    xmin = {}
    xmax = {}
    ymin = {}
    ymax = {}
    xspan = {}
    yspan = {}

    for f in families:
        for k in range(n):
            xmin[f, k] = model.new_int_var(0, max_W, f"xmin[{f},{k}]")
            xmax[f, k] = model.new_int_var(0, max_W, f"xmax[{f},{k}]")
            ymin[f, k] = model.new_int_var(0, max_D, f"ymin[{f},{k}]")
            ymax[f, k] = model.new_int_var(0, max_D, f"ymax[{f},{k}]")

            xspan[f, k] = model.new_int_var(0, max_W, f"xspan[{f},{k}]")
            yspan[f, k] = model.new_int_var(0, max_D, f"yspan[{f},{k}]")

    for i, item in enumerate(items):
        f = item.family
        for k in range(i + 1):
            model.add(xmin[f, k] <= x[i]).only_enforce_if(is_in[i, k])
            model.add(xmax[f, k] >= x[i] + item.w).only_enforce_if(is_in[i, k])
            model.add(ymin[f, k] <= y[i]).only_enforce_if(is_in[i, k])
            model.add(ymax[f, k] >= y[i] + item.d).only_enforce_if(is_in[i, k])

    for f in families:
        for k in range(n):
            model.add(xspan[f, k] == xmax[f, k] - xmin[f, k])
            model.add(yspan[f, k] == ymax[f, k] - ymin[f, k])

    for f in families:
        for k in range(n):
            model.add(xspan[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())
            model.add(yspan[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())

    for f in families:
        for k in range(n):
            model.add(xmin[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())
            model.add(xmax[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())
            model.add(ymin[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())
            model.add(ymax[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())

    return xspan, yspan


def add_non_overlap_constraints(model: cp_model.CpModel, items: list[Item], variables: dict, separator: int):
    n = len(items)
    bin_of = variables["bin_of"]
    x = variables["x"]
    y = variables["y"]

    for i in range(n):
        wi = items[i].w
        di = items[i].d
        for j in range(i + 1, n):
            wj = items[j].w
            dj = items[j].d

            same_bin = model.new_bool_var(f"same_bin[{i},{j}]")
            model.add(bin_of[i] == bin_of[j]).only_enforce_if(same_bin)
            model.add(bin_of[i] != bin_of[j]).only_enforce_if(same_bin.Not())

            left_ij = model.new_bool_var(f"left[{i},{j}]")
            left_ji = model.new_bool_var(f"left[{j},{i}]")
            below_ij = model.new_bool_var(f"below[{i},{j}]")
            below_ji = model.new_bool_var(f"below[{j},{i}]")

            model.add_bool_or([left_ij, left_ji, below_ij, below_ji, same_bin.Not()])

            model.add(x[i] + wi + separator <= x[j]).only_enforce_if(left_ij)
            model.add(x[j] + wj + separator <= x[i]).only_enforce_if(left_ji)
            model.add(y[i] + di + separator <= y[j]).only_enforce_if(below_ij)
            model.add(y[j] + dj + separator <= y[i]).only_enforce_if(below_ji)

            model.add_implication(left_ij, same_bin)
            model.add_implication(left_ji, same_bin)
            model.add_implication(below_ij, same_bin)
            model.add_implication(below_ji, same_bin)


def build_objective(model: cp_model.CpModel, families, variables: dict, family_drawer_count: dict, xspan: dict, yspan: dict, config: SolverConfig):
    n_items = len(variables["bin_of"])
    num_bins = variables["num_bins"]

    model.minimize(
        config.bin_weight * num_bins
        + config.family_weight * sum(family_drawer_count[f] for f in families)
        + config.span_weight * sum(xspan[f, k] + yspan[f, k] for f in families for k in range(n_items))
    )


def build_model(items: list[Item], families, bin_types: list[tuple[int, int]], config: SolverConfig):
    model = cp_model.CpModel()

    variables = create_variables(model, items, bin_types, families)

    is_in = add_placement_constraints(model, items, variables)
    fam_in_bin, family_drawer_count = add_family_constraints(model, items, families, is_in, variables)
    xspan, yspan = add_spatial_span_constraints(model, items, families, is_in, fam_in_bin, variables)
    add_non_overlap_constraints(model, items, variables, config.separator)

    build_objective(model, families, variables, family_drawer_count, xspan, yspan, config)

    return model, variables
