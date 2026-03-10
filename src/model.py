from ortools.sat.python import cp_model

from src.types import Item, BinType, Geometry, SolverConfig


def create_variables(model: cp_model.CpModel, items: list[Item], bin_types: list[BinType], families, geometry: Geometry):
    num_items = len(items)
    num_bin_types = len(bin_types)

    max_W = max(bt.W for bt in bin_types)
    max_D = max(bt.D for bt in bin_types)

    num_bins = model.new_int_var(1, num_items, "num_bins") ## Todo : faire une heuristque qui calcule le nombre max de bins(genre 1 famille par bins)

    bin_of = [model.new_int_var(0, i, f"bin_of[{i}]") for i in range(num_items)]
    x = [model.new_int_var(0, max_W, f"x[{i}]") for i in range(num_items)]
    y = [model.new_int_var(0, max_D, f"y[{i}]") for i in range(num_items)]

    bin_type = [model.new_int_var(0, num_bin_types - 1, f"bin_type[{k}]") for k in range(num_items)]

    W_values = [bt.W for bt in bin_types]
    D_values = [bt.D for bt in bin_types]
    H_values = [bt.H for bt in bin_types]
    max_weight_values = [bt.max_weight for bt in bin_types]

    W_of_bin = [model.new_int_var(min(W_values), max(W_values), f"W_of_bin[{k}]") for k in range(num_items)]
    D_of_bin = [model.new_int_var(min(D_values), max(D_values), f"D_of_bin[{k}]") for k in range(num_items)]
    H_of_bin = [model.new_int_var(min(H_values), max(H_values), f"H_of_bin[{k}]") for k in range(num_items)]
    max_weight_of_bin = [model.new_int_var(min(max_weight_values), max(max_weight_values), f"max_weight_of_bin[{k}]") for k in range(num_items)]

    for k in range(num_items):
        model.add_element(bin_type[k], W_values, W_of_bin[k])
        model.add_element(bin_type[k], D_values, D_of_bin[k])
        model.add_element(bin_type[k], H_values, H_of_bin[k])
        model.add_element(bin_type[k], max_weight_values, max_weight_of_bin[k])

    # Variant selection
    variant_of = []
    eff_w = []
    eff_d = []
    eff_h = []

    for i, item in enumerate(items):
        num_variants = len(item.variants)
        w_values = [v.w for v in item.variants]
        d_values = [v.d for v in item.variants]
        h_values = [v.h for v in item.variants]

        variant_of_i = model.new_int_var(0, num_variants - 1, f"variant_of[{i}]")
        eff_w_i = model.new_int_var(min(w_values), max(w_values), f"eff_w[{i}]")
        eff_d_i = model.new_int_var(min(d_values), max(d_values), f"eff_d[{i}]")
        eff_h_i = model.new_int_var(min(h_values), max(h_values), f"eff_h[{i}]")

        model.add_element(variant_of_i, w_values, eff_w_i)
        model.add_element(variant_of_i, d_values, eff_d_i)
        model.add_element(variant_of_i, h_values, eff_h_i)

        variant_of.append(variant_of_i)
        eff_w.append(eff_w_i)
        eff_d.append(eff_d_i)
        eff_h.append(eff_h_i)

    # Occupied height: max between nominal bin height and tallest item inside
    max_H = max(H_values)
    max_item_h = max(v.h for item in items for v in item.variants)
    occ_h_ub = max(max_H, max_item_h)
    occupied_height_of_bin = [model.new_int_var(0, occ_h_ub, f"occupied_height_of_bin[{k}]") for k in range(num_items)]

    # Bin used flag
    used_bin = [model.new_bool_var(f"used_bin[{k}]") for k in range(num_items)]

    # Cabinet variables
    max_num_cabinets = num_items  # upper bound
    num_cabinets = model.new_int_var(1, max_num_cabinets, "num_cabinets")
    cabinet_of_bin = [model.new_int_var(0, max_num_cabinets - 1, f"cabinet_of_bin[{k}]") for k in range(num_items)]
    Z_of_bin = [model.new_int_var(0, geometry.cabinet_height, f"Z_of_bin[{k}]") for k in range(num_items)]

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
        "max_weight_of_bin": max_weight_of_bin,
        "variant_of": variant_of,
        "eff_w": eff_w,
        "eff_d": eff_d,
        "eff_h": eff_h,
        "H_of_bin": H_of_bin,
        "occupied_height_of_bin": occupied_height_of_bin,
        "used_bin": used_bin,
        "num_cabinets": num_cabinets,
        "cabinet_of_bin": cabinet_of_bin,
        "Z_of_bin": Z_of_bin,
    }


def add_placement_constraints(model: cp_model.CpModel, items: list[Item], variables: dict):
    num_items = len(items)
    bin_of = variables["bin_of"]
    x = variables["x"]
    y = variables["y"]
    num_bins = variables["num_bins"]
    W_of_bin = variables["W_of_bin"]
    D_of_bin = variables["D_of_bin"]
    eff_w = variables["eff_w"]
    eff_d = variables["eff_d"]

    model.add(bin_of[0] == 0)
    for i in range(num_items):
        model.add(bin_of[i] < num_bins)

    is_in = {}
    for i in range(num_items):
        for k in range(i + 1):
            is_in[i, k] = model.new_bool_var(f"is_in[{i},{k}]")
            model.add(bin_of[i] == k).only_enforce_if(is_in[i, k])
            model.add(bin_of[i] != k).only_enforce_if(is_in[i, k].Not())

            model.add(x[i] + eff_w[i] <= W_of_bin[k]).only_enforce_if(is_in[i, k])
            model.add(y[i] + eff_d[i] <= D_of_bin[k]).only_enforce_if(is_in[i, k])

    return is_in


def add_family_constraints(model: cp_model.CpModel, items: list[Item], families, is_in: dict, variables: dict):
    num_items = len(items)

    fam_in_bin = {}
    for f in families:
        for k in range(num_items):
            fam_in_bin[f, k] = model.new_bool_var(f"fam_{f}_in_bin_{k}")

    for i, item in enumerate(items):
        for k in range(i + 1):
            model.add_implication(is_in[i, k], fam_in_bin[item.family, k])

    for f in families:
        items_f = [i for i, item in enumerate(items) if item.family == f]

        for k in range(num_items):
            vars_in_bin = [is_in[i, k] for i in items_f if (i, k) in is_in]

            if vars_in_bin:
                model.add_max_equality(fam_in_bin[f, k], vars_in_bin)
            else:
                model.add(fam_in_bin[f, k] == 0)

    family_drawer_count = {}
    for f in families:
        family_drawer_count[f] = model.new_int_var(0, num_items, f"family_drawer_count_{f}")
        model.add(
            family_drawer_count[f] ==
            sum(fam_in_bin[f, k] for k in range(num_items))
        )

    return fam_in_bin, family_drawer_count


def add_spatial_span_constraints(model: cp_model.CpModel, items: list[Item], families, is_in: dict, fam_in_bin: dict, variables: dict):
    num_items = len(items)
    x = variables["x"]
    y = variables["y"]
    eff_w = variables["eff_w"]
    eff_d = variables["eff_d"]
    max_W = variables["max_W"]
    max_D = variables["max_D"]

    xmin = {}
    xmax = {}
    ymin = {}
    ymax = {}
    xspan = {}
    yspan = {}

    for f in families:
        for k in range(num_items):
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
            model.add(xmax[f, k] >= x[i] + eff_w[i]).only_enforce_if(is_in[i, k])
            model.add(ymin[f, k] <= y[i]).only_enforce_if(is_in[i, k])
            model.add(ymax[f, k] >= y[i] + eff_d[i]).only_enforce_if(is_in[i, k])

    for f in families:
        for k in range(num_items):
            model.add(xspan[f, k] == xmax[f, k] - xmin[f, k])
            model.add(yspan[f, k] == ymax[f, k] - ymin[f, k])

    for f in families:
        for k in range(num_items):
            model.add(xspan[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())
            model.add(yspan[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())

    for f in families:
        for k in range(num_items):
            model.add(xmin[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())
            model.add(xmax[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())
            model.add(ymin[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())
            model.add(ymax[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())

    return xspan, yspan


def add_non_overlap_constraints(model: cp_model.CpModel, items: list[Item], variables: dict, separator: int):
    num_items = len(items)
    bin_of = variables["bin_of"]
    x = variables["x"]
    y = variables["y"]
    eff_w = variables["eff_w"]
    eff_d = variables["eff_d"]

    for i in range(num_items):
        for j in range(i + 1, num_items):
            same_bin = model.new_bool_var(f"same_bin[{i},{j}]")
            model.add(bin_of[i] == bin_of[j]).only_enforce_if(same_bin)
            model.add(bin_of[i] != bin_of[j]).only_enforce_if(same_bin.Not())

            left_ij = model.new_bool_var(f"left[{i},{j}]")
            left_ji = model.new_bool_var(f"left[{j},{i}]")
            below_ij = model.new_bool_var(f"below[{i},{j}]")
            below_ji = model.new_bool_var(f"below[{j},{i}]")

            model.add_bool_or([left_ij, left_ji, below_ij, below_ji, same_bin.Not()])

            model.add(x[i] + eff_w[i] + separator <= x[j]).only_enforce_if(left_ij)
            model.add(x[j] + eff_w[j] + separator <= x[i]).only_enforce_if(left_ji)
            model.add(y[i] + eff_d[i] + separator <= y[j]).only_enforce_if(below_ij)
            model.add(y[j] + eff_d[j] + separator <= y[i]).only_enforce_if(below_ji)

            model.add_implication(left_ij, same_bin)
            model.add_implication(left_ji, same_bin)
            model.add_implication(below_ij, same_bin)
            model.add_implication(below_ji, same_bin)


def add_weight_constraints(model: cp_model.CpModel, items: list[Item], is_in: dict, variables: dict):
    num_items = len(items)
    max_weight_of_bin = variables["max_weight_of_bin"]

    for k in range(num_items):
        weighted_items = [
            items[i].weight * is_in[i, k]
            for i in range(num_items)
            if (i, k) in is_in
        ]
        if weighted_items:
            model.add(sum(weighted_items) <= max_weight_of_bin[k])


def add_bin_height_constraints(model: cp_model.CpModel, items: list[Item], is_in: dict, variables: dict):
    num_items = len(items)
    eff_h = variables["eff_h"]
    H_of_bin = variables["H_of_bin"]
    occupied_height_of_bin = variables["occupied_height_of_bin"]
    used_bin = variables["used_bin"]

    # Each item can exceed the bin height by up to 30%: eff_h[i] <= 1.3 * H_of_bin[k]
    # Integer formulation: 10 * eff_h[i] <= 13 * H_of_bin[k]
    for i in range(num_items):
        for k in range(i + 1):
            if (i, k) in is_in:
                model.add(10 * eff_h[i] <= 13 * H_of_bin[k]).only_enforce_if(is_in[i, k])

    # occupied_height_of_bin[k] >= H_of_bin[k] (at least the nominal height)
    for k in range(num_items):
        model.add(occupied_height_of_bin[k] >= H_of_bin[k]).only_enforce_if(used_bin[k])
        model.add(occupied_height_of_bin[k] == 0).only_enforce_if(used_bin[k].Not())

    # occupied_height_of_bin[k] >= eff_h[i] for every item i in bin k
    for i in range(num_items):
        for k in range(i + 1):
            if (i, k) in is_in:
                model.add(occupied_height_of_bin[k] >= eff_h[i]).only_enforce_if(is_in[i, k])

    # used_bin[k] == 1 iff at least one item is in bin k
    for k in range(num_items):
        items_in_k = [is_in[i, k] for i in range(num_items) if (i, k) in is_in]
        if items_in_k:
            model.add_max_equality(used_bin[k], items_in_k)
        else:
            model.add(used_bin[k] == 0)


def add_cabinet_constraints(model: cp_model.CpModel, items: list[Item], variables: dict, geometry: Geometry):
    num_items = len(items)
    used_bin = variables["used_bin"]
    occupied_height_of_bin = variables["occupied_height_of_bin"]
    Z_of_bin = variables["Z_of_bin"]
    num_cabinets = variables["num_cabinets"]
    cabinet_of_bin = variables["cabinet_of_bin"]
    cabinet_height = geometry.cabinet_height

    # Used bins must be in a valid cabinet
    # Unused bins: z=0, cabinet=0 (no impact)
    for k in range(num_items):
        model.add(cabinet_of_bin[k] < num_cabinets).only_enforce_if(used_bin[k])
        model.add(cabinet_of_bin[k] == 0).only_enforce_if(used_bin[k].Not())
        model.add(Z_of_bin[k] == 0).only_enforce_if(used_bin[k].Not())

    # Each used bin must fit within the cabinet height (using occupied height)
    for k in range(num_items):
        model.add(Z_of_bin[k] + occupied_height_of_bin[k] <= cabinet_height).only_enforce_if(used_bin[k])

    # Non-overlapping on Z axis for bins in the same cabinet
    for k in range(num_items):
        for l in range(k + 1, num_items):
            same_cabinet = model.new_bool_var(f"same_cabinet[{k},{l}]")
            model.add(cabinet_of_bin[k] == cabinet_of_bin[l]).only_enforce_if(same_cabinet)
            model.add(cabinet_of_bin[k] != cabinet_of_bin[l]).only_enforce_if(same_cabinet.Not())

            # Both must be used and in the same cabinet to need separation
            both_used_same = model.new_bool_var(f"both_used_same[{k},{l}]")
            model.add_bool_and([used_bin[k], used_bin[l], same_cabinet]).only_enforce_if(both_used_same)
            model.add_bool_or([used_bin[k].Not(), used_bin[l].Not(), same_cabinet.Not()]).only_enforce_if(both_used_same.Not())

            k_above_l = model.new_bool_var(f"k_above_l[{k},{l}]")
            l_above_k = model.new_bool_var(f"l_above_k[{k},{l}]")

            model.add(Z_of_bin[l] + occupied_height_of_bin[l] <= Z_of_bin[k]).only_enforce_if(k_above_l)
            model.add(Z_of_bin[k] + occupied_height_of_bin[k] <= Z_of_bin[l]).only_enforce_if(l_above_k)

            model.add_bool_or([k_above_l, l_above_k, both_used_same.Not()])

            model.add_implication(k_above_l, both_used_same)
            model.add_implication(l_above_k, both_used_same)


def build_objective(model: cp_model.CpModel, families, variables: dict, family_drawer_count: dict, xspan: dict, yspan: dict, config: SolverConfig):
    num_items = len(variables["bin_of"])
    num_bins = variables["num_bins"]
    num_cabinets = variables["num_cabinets"]

    model.minimize(
        config.cabinet_weight * num_cabinets
        + config.bin_weight * num_bins
        + config.family_weight * sum(family_drawer_count[f] for f in families)
        + config.span_weight * sum(xspan[f, k] + yspan[f, k] for f in families for k in range(num_items))
    )


def build_model(items: list[Item], families, bin_types: list[BinType], geometry: Geometry, config: SolverConfig):
    model = cp_model.CpModel()

    variables = create_variables(model, items, bin_types, families, geometry)

    is_in = add_placement_constraints(model, items, variables)
    fam_in_bin, family_drawer_count = add_family_constraints(model, items, families, is_in, variables)
    xspan, yspan = add_spatial_span_constraints(model, items, families, is_in, fam_in_bin, variables)
    add_non_overlap_constraints(model, items, variables, geometry.separator)
    add_weight_constraints(model, items, is_in, variables)
    add_bin_height_constraints(model, items, is_in, variables)
    add_cabinet_constraints(model, items, variables, geometry)

    build_objective(model, families, variables, family_drawer_count, xspan, yspan, config)

    return model, variables
