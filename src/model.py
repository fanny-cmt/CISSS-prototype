from ortools.sat.python import cp_model

from src.types import Item, BinType, Geometry, SolverConfig


def create_variables(model: cp_model.CpModel, items: list[Item], bin_types: list[BinType], families, geometry: Geometry, max_bins: int | None = None, max_cabinets: int | None = None):
    num_items = len(items)
    num_bin_types = len(bin_types)
    max_bin_slots = min(max_bins, num_items) if max_bins is not None else num_items

    max_W = max(bt.W for bt in bin_types)
    max_D = max(bt.D for bt in bin_types)

    num_bins = model.new_int_var(1, max_bin_slots, "num_bins")

    bin_of = [model.new_int_var(0, min(i, max_bin_slots - 1), f"bin_of[{i}]") for i in range(num_items)]
    x = [model.new_int_var(0, max_W, f"x[{i}]") for i in range(num_items)]
    y = [model.new_int_var(0, max_D, f"y[{i}]") for i in range(num_items)]

    bin_type = [model.new_int_var(0, num_bin_types - 1, f"bin_type[{k}]") for k in range(max_bin_slots)]

    W_values = [bt.W for bt in bin_types]
    D_values = [bt.D for bt in bin_types]
    H_values = [bt.H for bt in bin_types]
    max_weight_values = [bt.max_weight for bt in bin_types]

    area_values = [bt.W * bt.D for bt in bin_types]

    W_of_bin = [model.new_int_var(min(W_values), max(W_values), f"W_of_bin[{k}]") for k in range(max_bin_slots)]
    D_of_bin = [model.new_int_var(min(D_values), max(D_values), f"D_of_bin[{k}]") for k in range(max_bin_slots)]
    H_of_bin = [model.new_int_var(min(H_values), max(H_values), f"H_of_bin[{k}]") for k in range(max_bin_slots)]
    max_weight_of_bin = [model.new_int_var(min(max_weight_values), max(max_weight_values), f"max_weight_of_bin[{k}]") for k in range(max_bin_slots)]
    area_of_bin = [model.new_int_var(min(area_values), max(area_values), f"area_of_bin[{k}]") for k in range(max_bin_slots)]

    for k in range(max_bin_slots):
        model.add_element(bin_type[k], W_values, W_of_bin[k])
        model.add_element(bin_type[k], D_values, D_of_bin[k])
        model.add_element(bin_type[k], H_values, H_of_bin[k])
        model.add_element(bin_type[k], max_weight_values, max_weight_of_bin[k])
        model.add_element(bin_type[k], area_values, area_of_bin[k])

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
    occupied_height_of_bin = [model.new_int_var(0, occ_h_ub, f"occupied_height_of_bin[{k}]") for k in range(max_bin_slots)]

    # Bin used flag
    used_bin = [model.new_bool_var(f"used_bin[{k}]") for k in range(max_bin_slots)]

    # Cabinet variables
    max_cabinet_slots = min(max_cabinets, max_bin_slots) if max_cabinets is not None else max_bin_slots
    num_cabinets = model.new_int_var(0, max_cabinet_slots, "num_cabinets")
    cabinet_of_bin = [model.new_int_var(0, max_cabinet_slots - 1, f"cabinet_of_bin[{k}]") for k in range(max_bin_slots)]
    Z_of_bin = [model.new_int_var(0, geometry.cabinet_height, f"Z_of_bin[{k}]") for k in range(max_bin_slots)]
    used_cabinet = [model.new_bool_var(f"used_cabinet[{c}]") for c in range(max_cabinet_slots)]

    return {
        "max_bin_slots": max_bin_slots,
        "max_cabinet_slots": max_cabinet_slots,
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
        "area_of_bin": area_of_bin,
        "variant_of": variant_of,
        "eff_w": eff_w,
        "eff_d": eff_d,
        "eff_h": eff_h,
        "H_of_bin": H_of_bin,
        "occupied_height_of_bin": occupied_height_of_bin,
        "occ_h_ub": occ_h_ub,
        "used_bin": used_bin,
        "num_cabinets": num_cabinets,
        "cabinet_of_bin": cabinet_of_bin,
        "Z_of_bin": Z_of_bin,
        "used_cabinet": used_cabinet,
        "min_bin_height": min(H_values),
    }


def add_placement_constraints(model: cp_model.CpModel, items: list[Item], variables: dict):
    num_items = len(items)
    max_bin_slots = variables["max_bin_slots"]
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
        for k in range(min(i + 1, max_bin_slots)):
            is_in[i, k] = model.new_bool_var(f"is_in[{i},{k}]")
            model.add(bin_of[i] == k).only_enforce_if(is_in[i, k])
            model.add(bin_of[i] != k).only_enforce_if(is_in[i, k].Not())

            model.add(x[i] + eff_w[i] <= W_of_bin[k]).only_enforce_if(is_in[i, k])
            model.add(y[i] + eff_d[i] <= D_of_bin[k]).only_enforce_if(is_in[i, k])

    return is_in


def add_family_constraints(model: cp_model.CpModel, items: list[Item], families, is_in: dict, variables: dict):
    max_bin_slots = variables["max_bin_slots"]

    fam_in_bin = {}
    for f in families:
        for k in range(max_bin_slots):
            fam_in_bin[f, k] = model.new_bool_var(f"fam_{f}_in_bin_{k}")

    for f in families:
        items_f = [i for i, item in enumerate(items) if item.family == f]

        for k in range(max_bin_slots):
            vars_in_bin = [is_in[i, k] for i in items_f if (i, k) in is_in]

            if vars_in_bin:
                model.add_max_equality(fam_in_bin[f, k], vars_in_bin)
            else:
                model.add(fam_in_bin[f, k] == 0)

    family_drawer_count = {}
    for f in families:
        family_drawer_count[f] = model.new_int_var(0, max_bin_slots, f"family_drawer_count_{f}")
        model.add(
            family_drawer_count[f] ==
            sum(fam_in_bin[f, k] for k in range(max_bin_slots))
        )

    return fam_in_bin, family_drawer_count


def add_spatial_span_constraints(model: cp_model.CpModel, items: list[Item], families, is_in: dict, fam_in_bin: dict, variables: dict, config: SolverConfig):
    if config.span_weight == 0:
        return {}, {}

    max_bin_slots = variables["max_bin_slots"]
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
        for k in range(max_bin_slots):
            xmin[f, k] = model.new_int_var(0, max_W, f"xmin[{f},{k}]")
            xmax[f, k] = model.new_int_var(0, max_W, f"xmax[{f},{k}]")
            ymin[f, k] = model.new_int_var(0, max_D, f"ymin[{f},{k}]")
            ymax[f, k] = model.new_int_var(0, max_D, f"ymax[{f},{k}]")

            xspan[f, k] = model.new_int_var(0, max_W, f"xspan[{f},{k}]")
            yspan[f, k] = model.new_int_var(0, max_D, f"yspan[{f},{k}]")

    for i, item in enumerate(items):
        f = item.family
        for k in range(min(i + 1, max_bin_slots)):
            model.add(xmin[f, k] <= x[i]).only_enforce_if(is_in[i, k])
            model.add(xmax[f, k] >= x[i] + eff_w[i]).only_enforce_if(is_in[i, k])
            model.add(ymin[f, k] <= y[i]).only_enforce_if(is_in[i, k])
            model.add(ymax[f, k] >= y[i] + eff_d[i]).only_enforce_if(is_in[i, k])

    for f in families:
        for k in range(max_bin_slots):
            model.add(xspan[f, k] == xmax[f, k] - xmin[f, k])
            model.add(yspan[f, k] == ymax[f, k] - ymin[f, k])

    for f in families:
        for k in range(max_bin_slots):
            model.add(xspan[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())
            model.add(yspan[f, k] == 0).only_enforce_if(fam_in_bin[f, k].Not())

    for f in families:
        for k in range(max_bin_slots):
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


def add_non_overlap_constraints_global(model: cp_model.CpModel, items: list[Item], is_in: dict, variables: dict, separator: int):
    """Non-overlap using one AddNoOverlap2D per bin slot with optional interval variables."""
    num_items = len(items)
    max_bin_slots = variables["max_bin_slots"]
    x = variables["x"]
    y = variables["y"]
    eff_w = variables["eff_w"]
    eff_d = variables["eff_d"]
    max_W = variables["max_W"]
    max_D = variables["max_D"]

    for k in range(max_bin_slots):
        x_intervals = []
        y_intervals = []

        for i in range(num_items):
            if (i, k) not in is_in:
                continue

            # Size includes separator so NoOverlap2D enforces the gap
            size_x = model.new_int_var(0, max_W + separator, f"sx[{i},{k}]")
            size_y = model.new_int_var(0, max_D + separator, f"sy[{i},{k}]")
            end_x = model.new_int_var(0, 2 * max_W + separator, f"ex[{i},{k}]")
            end_y = model.new_int_var(0, 2 * max_D + separator, f"ey[{i},{k}]")

            model.add(size_x == eff_w[i] + separator).only_enforce_if(is_in[i, k])
            model.add(size_x == 0).only_enforce_if(is_in[i, k].Not())
            model.add(size_y == eff_d[i] + separator).only_enforce_if(is_in[i, k])
            model.add(size_y == 0).only_enforce_if(is_in[i, k].Not())

            model.add(end_x == x[i] + size_x)
            model.add(end_y == y[i] + size_y)

            ix = model.new_optional_interval_var(
                x[i], size_x, end_x, is_in[i, k], f"ix[{i},{k}]"
            )
            iy = model.new_optional_interval_var(
                y[i], size_y, end_y, is_in[i, k], f"iy[{i},{k}]"
            )
            x_intervals.append(ix)
            y_intervals.append(iy)

        if x_intervals:
            model.add_no_overlap_2d(x_intervals, y_intervals)


def add_weight_constraints(model: cp_model.CpModel, items: list[Item], is_in: dict, variables: dict):
    max_bin_slots = variables["max_bin_slots"]
    max_weight_of_bin = variables["max_weight_of_bin"]

    for k in range(max_bin_slots):
        weighted_items = [
            items[i].weight * is_in[i, k]
            for i in range(len(items))
            if (i, k) in is_in
        ]
        if weighted_items:
            model.add(sum(weighted_items) <= max_weight_of_bin[k])


def add_bin_height_constraints(model: cp_model.CpModel, items: list[Item], is_in: dict, variables: dict):
    num_items = len(items)
    max_bin_slots = variables["max_bin_slots"]
    eff_h = variables["eff_h"]
    H_of_bin = variables["H_of_bin"]
    bin_type = variables["bin_type"]
    occupied_height_of_bin = variables["occupied_height_of_bin"]
    used_bin = variables["used_bin"]
    num_bins = variables["num_bins"]
    max_h_ub = variables["occ_h_ub"]

    # 1) Height tolerance: item may exceed bin height by up to 30%
    #    Integer formulation: 10 * eff_h[i] <= 13 * H_of_bin[k]
    for i in range(num_items):
        for k in range(min(i + 1, max_bin_slots)):
            if (i, k) in is_in:
                model.add(10 * eff_h[i] <= 13 * H_of_bin[k]).only_enforce_if(is_in[i, k])

    # 2) used_bin[k] == 1 iff at least one item is in bin k
    for k in range(max_bin_slots):
        items_in_k = [is_in[i, k] for i in range(num_items) if (i, k) in is_in]
        if items_in_k:
            model.add_max_equality(used_bin[k], items_in_k)
        else:
            model.add(used_bin[k] == 0)

    # 3) Bin compaction: used bins form a contiguous prefix
    for k in range(max_bin_slots - 1):
        model.add(used_bin[k] >= used_bin[k + 1])

    # 4) num_bins is the exact count of used bins
    model.add(num_bins == sum(used_bin))

    # 5) Fix unused bin variables to reduce symmetry
    for k in range(max_bin_slots):
        model.add(bin_type[k] == 0).only_enforce_if(used_bin[k].Not())

    # 6) Exact occupied_height_of_bin via add_max_equality
    for k in range(max_bin_slots):
        # Nominal height: H_of_bin[k] if used, 0 otherwise
        h_nominal = model.new_int_var(0, max_h_ub, f"h_nominal[{k}]")
        model.add(h_nominal == H_of_bin[k]).only_enforce_if(used_bin[k])
        model.add(h_nominal == 0).only_enforce_if(used_bin[k].Not())

        # Per-item contributions: eff_h[i] if in bin k, 0 otherwise
        max_args = [h_nominal]
        for i in range(num_items):
            if (i, k) in is_in:
                h_contrib = model.new_int_var(0, max_h_ub, f"h_contrib[{i},{k}]")
                model.add(h_contrib == eff_h[i]).only_enforce_if(is_in[i, k])
                model.add(h_contrib == 0).only_enforce_if(is_in[i, k].Not())
                max_args.append(h_contrib)

        model.add_max_equality(occupied_height_of_bin[k], max_args)


def add_area_constraints(model: cp_model.CpModel, items: list[Item], is_in: dict, variables: dict):
    max_bin_slots = variables["max_bin_slots"]
    area_of_bin = variables["area_of_bin"]

    # item_area[i] linked to variant_of[i] via add_element
    item_area = []
    for i, item in enumerate(items):
        area_values_i = [v.w * v.d for v in item.variants]
        area_i = model.new_int_var(min(area_values_i), max(area_values_i), f"item_area[{i}]")
        model.add_element(variables["variant_of"][i], area_values_i, area_i)
        item_area.append(area_i)

    # Sum of item areas in each bin must not exceed the bin's area
    for k in range(max_bin_slots):
        area_terms = []
        for i in range(len(items)):
            if (i, k) in is_in:
                # area_i * is_in[i,k]: use intermediate variable
                contrib = model.new_int_var(0, max(v.w * v.d for v in items[i].variants), f"area_contrib[{i},{k}]")
                model.add(contrib == item_area[i]).only_enforce_if(is_in[i, k])
                model.add(contrib == 0).only_enforce_if(is_in[i, k].Not())
                area_terms.append(contrib)
        if area_terms:
            model.add(sum(area_terms) <= area_of_bin[k])


def add_cabinet_constraints(model: cp_model.CpModel, items: list[Item], variables: dict, geometry: Geometry):
    max_bin_slots = variables["max_bin_slots"]
    max_cabinet_slots = variables["max_cabinet_slots"]
    used_bin = variables["used_bin"]
    occupied_height_of_bin = variables["occupied_height_of_bin"]
    Z_of_bin = variables["Z_of_bin"]
    num_cabinets = variables["num_cabinets"]
    cabinet_of_bin = variables["cabinet_of_bin"]
    used_cabinet = variables["used_cabinet"]
    cabinet_height = geometry.cabinet_height
    drawer_gap = geometry.drawer_gap

    # Symmetry breaking: bin k can only use cabinets 0..k (capped by max_cabinet_slots)
    for k in range(max_bin_slots):
        model.add(cabinet_of_bin[k] <= min(k, max_cabinet_slots - 1))

    # Link used bins to valid cabinet indices
    for k in range(max_bin_slots):
        model.add(cabinet_of_bin[k] < num_cabinets).only_enforce_if(used_bin[k])
        model.add(cabinet_of_bin[k] == 0).only_enforce_if(used_bin[k].Not())
        model.add(Z_of_bin[k] == 0).only_enforce_if(used_bin[k].Not())

    # Each used bin must fit inside cabinet height
    for k in range(max_bin_slots):
        model.add(
            Z_of_bin[k] + occupied_height_of_bin[k] <= cabinet_height
        ).only_enforce_if(used_bin[k])

    # bin_in_cabinet[k, c] means: bin k is used and assigned to cabinet c
    bin_in_cabinet = {}
    for k in range(max_bin_slots):
        cabinet_choices_k = []

        for c in range(min(k + 1, max_cabinet_slots)):
            b = model.new_bool_var(f"bin_in_cabinet[{k},{c}]")
            bin_in_cabinet[k, c] = b
            cabinet_choices_k.append(b)

            # b => used_bin[k] and cabinet_of_bin[k] == c
            model.add(cabinet_of_bin[k] == c).only_enforce_if(b)
            model.add(used_bin[k] == 1).only_enforce_if(b)


        # Exact assignment:
        # - if bin k is unused, no cabinet is selected
        # - if bin k is used, exactly one cabinet is selected
        model.add(sum(cabinet_choices_k) == used_bin[k])

    # used_cabinet[c] = OR of all bin_in_cabinet[k, c]
    for c in range(max_cabinet_slots):
        bins_in_c = [
            bin_in_cabinet[k, c]
            for k in range(max_bin_slots)
            if (k, c) in bin_in_cabinet
        ]
        if bins_in_c:
            model.add_max_equality(used_cabinet[c], bins_in_c)
        else:
            model.add(used_cabinet[c] == 0)

    # Cabinets must be used contiguously: 0,1,2,...
    for c in range(max_cabinet_slots - 1):
        model.add(used_cabinet[c] >= used_cabinet[c + 1])

    # Exact count of used cabinets
    model.add(num_cabinets == sum(used_cabinet))

    # Global valid inequality on total stacked height
    model.add(
        sum(occupied_height_of_bin[k] for k in range(max_bin_slots))
        + drawer_gap * (sum(used_bin) - num_cabinets)
        <= cabinet_height * num_cabinets
    )

    # Lower bound on num_cabinets from bin count and minimum bin height
    min_bin_height = variables["min_bin_height"]
    model.add(
        (cabinet_height + drawer_gap) * num_cabinets
        >= (min_bin_height + drawer_gap) * sum(used_bin)
    )

    return bin_in_cabinet


def add_cabinet_z_nooverlap(model: cp_model.CpModel, variables: dict, geometry: Geometry):
    """Pairwise Z-axis non-overlap for bins in the same cabinet."""
    max_bin_slots = variables["max_bin_slots"]
    used_bin = variables["used_bin"]
    occupied_height_of_bin = variables["occupied_height_of_bin"]
    Z_of_bin = variables["Z_of_bin"]
    cabinet_of_bin = variables["cabinet_of_bin"]
    drawer_gap = geometry.drawer_gap

    for k in range(max_bin_slots):
        for m in range(k + 1, max_bin_slots):
            same_cabinet = model.new_bool_var(f"same_cabinet[{k},{m}]")
            model.add(cabinet_of_bin[k] == cabinet_of_bin[m]).only_enforce_if(same_cabinet)
            model.add(cabinet_of_bin[k] != cabinet_of_bin[m]).only_enforce_if(same_cabinet.Not())

            k_above_m = model.new_bool_var(f"k_above_m[{k},{m}]")
            m_above_k = model.new_bool_var(f"m_above_k[{k},{m}]")

            model.add(
                Z_of_bin[m] + occupied_height_of_bin[m] + drawer_gap <= Z_of_bin[k]
            ).only_enforce_if(k_above_m)
            model.add(
                Z_of_bin[k] + occupied_height_of_bin[k] + drawer_gap <= Z_of_bin[m]
            ).only_enforce_if(m_above_k)

            model.add_bool_or([
                k_above_m,
                m_above_k,
                used_bin[k].Not(),
                used_bin[m].Not(),
                same_cabinet.Not(),
            ])

            model.add_implication(k_above_m, used_bin[k])
            model.add_implication(k_above_m, used_bin[m])
            model.add_implication(k_above_m, same_cabinet)

            model.add_implication(m_above_k, used_bin[k])
            model.add_implication(m_above_k, used_bin[m])
            model.add_implication(m_above_k, same_cabinet)


def add_cabinet_z_nooverlap_global(model: cp_model.CpModel, bin_in_cabinet: dict, variables: dict, geometry: Geometry):
    """Z-axis non-overlap using one NoOverlap per cabinet with optional interval variables."""
    max_bin_slots = variables["max_bin_slots"]
    max_cabinet_slots = variables["max_cabinet_slots"]
    Z_of_bin = variables["Z_of_bin"]
    occupied_height_of_bin = variables["occupied_height_of_bin"]
    cabinet_height = geometry.cabinet_height
    drawer_gap = geometry.drawer_gap
    occ_h_ub = variables["occ_h_ub"]

    for c in range(max_cabinet_slots):
        intervals = []

        for k in range(max_bin_slots):
            if (k, c) not in bin_in_cabinet:
                continue

            # Size = occupied_height + drawer_gap (gap acts as spacing)
            size_z = model.new_int_var(0, occ_h_ub + drawer_gap, f"sz_cab[{k},{c}]")
            end_z = model.new_int_var(0, cabinet_height + drawer_gap, f"ez_cab[{k},{c}]")

            model.add(size_z == occupied_height_of_bin[k] + drawer_gap).only_enforce_if(bin_in_cabinet[k, c])
            model.add(size_z == 0).only_enforce_if(bin_in_cabinet[k, c].Not())
            model.add(end_z == Z_of_bin[k] + size_z)

            iv = model.new_optional_interval_var(
                Z_of_bin[k], size_z, end_z, bin_in_cabinet[k, c], f"iz_cab[{k},{c}]"
            )
            intervals.append(iv)

        if intervals:
            model.add_no_overlap(intervals)


def add_heavy_item_constraints(model: cp_model.CpModel, items: list[Item], variables: dict, geometry: Geometry):
    """Create Z-height variables for heavy items.

    For each heavy item i, links heavy_z[i] to Z_of_bin[bin_of[i]]
    via add_element on the Z_of_bin array.

    Returns a list of heavy_z variables for use in the objective.
    """
    heavy_indices = [i for i, item in enumerate(items) if item.heavy]
    if not heavy_indices:
        return []

    bin_of = variables["bin_of"]
    Z_of_bin = variables["Z_of_bin"]

    heavy_z = []
    for i in heavy_indices:
        z_i = model.new_int_var(0, geometry.cabinet_height, f"heavy_z[{i}]")
        model.add_element(bin_of[i], Z_of_bin, z_i)
        heavy_z.append(z_i)

    return heavy_z


def add_visibility_constraints(model: cp_model.CpModel, fam_in_bin: dict, variables: dict, geometry: Geometry, visible_families: list[int], config: SolverConfig):
    """Create visibility deviation variables for visible families.

    For each visible family f present in bin k, the deviation measures:
      |center_of_bin_k - eye_level| (in doubled coordinates to stay integer)

    where center_of_bin_k = 2 * Z_of_bin[k] + occupied_height_of_bin[k]
    and target = 2 * eye_level.

    Returns a dict {(f, k): deviation_var} for use in the objective.
    """
    if not visible_families:
        return {}

    max_bin_slots = variables["max_bin_slots"]
    Z_of_bin = variables["Z_of_bin"]
    occupied_height_of_bin = variables["occupied_height_of_bin"]
    occ_h_ub = variables["occ_h_ub"]

    target = 2 * geometry.eye_level
    max_center = 2 * geometry.cabinet_height + occ_h_ub
    max_dev = max(max_center, target)

    visibility_deviation = {}
    for f in visible_families:
        for k in range(max_bin_slots):
            if (f, k) not in fam_in_bin:
                continue

            # center = 2*Z + occ_h (integer, avoids division by 2)
            center = model.new_int_var(0, max_center, f"vis_center[{f},{k}]")
            model.add(center == 2 * Z_of_bin[k] + occupied_height_of_bin[k])

            # diff = center - target (can be negative)
            diff = model.new_int_var(-max_dev, max_dev, f"vis_diff[{f},{k}]")
            model.add(diff == center - target)

            # dev = |diff|, active only if family f is in bin k
            dev = model.new_int_var(0, max_dev, f"vis_dev[{f},{k}]")
            model.add_abs_equality(dev, diff)

            # Conditional: deviation counts only if family is present in bin
            cond_dev = model.new_int_var(0, max_dev, f"vis_cdev[{f},{k}]")
            model.add(cond_dev == dev).only_enforce_if(fam_in_bin[f, k])
            model.add(cond_dev == 0).only_enforce_if(fam_in_bin[f, k].Not())

            visibility_deviation[f, k] = cond_dev

    return visibility_deviation


def add_family_proximity_objective_terms(model: cp_model.CpModel, families, fam_in_bin: dict, variables: dict, geometry: Geometry, config: SolverConfig):
    if (
        config.family_cabinet_span_weight == 0
        and config.family_height_span_weight == 0
    ):
        return {}, {}

    max_bin_slots = variables["max_bin_slots"]
    max_cabinet_slots = variables["max_cabinet_slots"]
    Z_of_bin = variables["Z_of_bin"]
    occupied_height_of_bin = variables["occupied_height_of_bin"]
    cabinet_of_bin = variables["cabinet_of_bin"]
    occ_h_ub = variables["occ_h_ub"]

    max_cabinet_idx = max_cabinet_slots - 1
    center_ub = 2 * geometry.cabinet_height + occ_h_ub

    # Doubled vertical center of each bin:
    # center = 2 * Z + occupied_height
    center_of_bin = []
    for k in range(max_bin_slots):
        center_k = model.new_int_var(0, center_ub, f"bin_center[{k}]")
        model.add(center_k == 2 * Z_of_bin[k] + occupied_height_of_bin[k])
        center_of_bin.append(center_k)

    family_cabinet_span = {}
    family_height_span = {}

    for f in families:
        # Whether family f appears in at least one bin.
        family_present = model.new_bool_var(f"family_present[{f}]")
        model.add_max_equality(
            family_present,
            [fam_in_bin[f, k] for k in range(max_bin_slots)],
        )

        cabinet_values_for_max = []
        cabinet_values_for_min = []
        center_values_for_max = []
        center_values_for_min = []

        for k in range(max_bin_slots):
            # Sentinels:
            # - for max: absent bins contribute 0
            # - for min: absent bins contribute upper bound
            cabinet_max_val = model.new_int_var(
                0, max_cabinet_idx, f"fam_cab_max_val[{f},{k}]"
            )
            cabinet_min_val = model.new_int_var(
                0, max_cabinet_idx, f"fam_cab_min_val[{f},{k}]"
            )
            center_max_val = model.new_int_var(
                0, center_ub, f"fam_center_max_val[{f},{k}]"
            )
            center_min_val = model.new_int_var(
                0, center_ub, f"fam_center_min_val[{f},{k}]"
            )

            model.add(cabinet_max_val == cabinet_of_bin[k]).only_enforce_if(fam_in_bin[f, k])
            model.add(cabinet_max_val == 0).only_enforce_if(fam_in_bin[f, k].Not())

            model.add(cabinet_min_val == cabinet_of_bin[k]).only_enforce_if(fam_in_bin[f, k])
            model.add(cabinet_min_val == max_cabinet_idx).only_enforce_if(fam_in_bin[f, k].Not())

            model.add(center_max_val == center_of_bin[k]).only_enforce_if(fam_in_bin[f, k])
            model.add(center_max_val == 0).only_enforce_if(fam_in_bin[f, k].Not())

            model.add(center_min_val == center_of_bin[k]).only_enforce_if(fam_in_bin[f, k])
            model.add(center_min_val == center_ub).only_enforce_if(fam_in_bin[f, k].Not())

            cabinet_values_for_max.append(cabinet_max_val)
            cabinet_values_for_min.append(cabinet_min_val)
            center_values_for_max.append(center_max_val)
            center_values_for_min.append(center_min_val)

        cabinet_max = model.new_int_var(0, max_cabinet_idx, f"family_cabinet_max[{f}]")
        cabinet_min = model.new_int_var(0, max_cabinet_idx, f"family_cabinet_min[{f}]")
        center_max = model.new_int_var(0, center_ub, f"family_center_max[{f}]")
        center_min = model.new_int_var(0, center_ub, f"family_center_min[{f}]")

        model.add_max_equality(cabinet_max, cabinet_values_for_max)
        model.add_min_equality(cabinet_min, cabinet_values_for_min)
        model.add_max_equality(center_max, center_values_for_max)
        model.add_min_equality(center_min, center_values_for_min)

        family_cabinet_span[f] = model.new_int_var(
            0, max_cabinet_idx, f"family_cabinet_span[{f}]"
        )
        family_height_span[f] = model.new_int_var(
            0, center_ub, f"family_height_span[{f}]"
        )

        # If family absent: spans are 0.
        model.add(family_cabinet_span[f] == 0).only_enforce_if(family_present.Not())
        model.add(family_height_span[f] == 0).only_enforce_if(family_present.Not())

        # If family present: spans are max - min.
        model.add(family_cabinet_span[f] == cabinet_max - cabinet_min).only_enforce_if(family_present)
        model.add(family_height_span[f] == center_max - center_min).only_enforce_if(family_present)

    return family_cabinet_span, family_height_span


def build_objective(model: cp_model.CpModel, families, variables: dict, family_drawer_count: dict, xspan: dict, yspan: dict, visibility_deviation: dict, heavy_z: list, family_cabinet_span: dict, family_height_span: dict, config: SolverConfig):
    max_bin_slots = variables["max_bin_slots"]

    obj = (
        config.cabinet_weight * sum(variables["used_cabinet"])
        + config.bin_weight * sum(variables["used_bin"])
        + config.family_weight * sum(family_drawer_count[f] for f in families)
    )

    if config.span_weight != 0 and xspan and yspan:
        obj += config.span_weight * sum(xspan[f, k] + yspan[f, k] for f in families for k in range(max_bin_slots))

    if visibility_deviation:
        obj += config.visibility_weight * sum(visibility_deviation.values())

    if heavy_z:
        obj += config.heavy_weight * sum(heavy_z)

    if family_cabinet_span:
        obj += config.family_cabinet_span_weight * sum(family_cabinet_span.values())

    if family_height_span:
        obj += config.family_height_span_weight * sum(family_height_span.values())

    model.minimize(obj)


def build_model(items: list[Item], families, bin_types: list[BinType], geometry: Geometry, config: SolverConfig, visible_families: list[int] | None = None, max_bins: int | None = None, max_cabinets: int | None = None):
    model = cp_model.CpModel()

    variables = create_variables(model, items, bin_types, families, geometry, max_bins, max_cabinets)

    is_in = add_placement_constraints(model, items, variables)
    fam_in_bin, family_drawer_count = add_family_constraints(model, items, families, is_in, variables)
    xspan, yspan = add_spatial_span_constraints(model, items, families, is_in, fam_in_bin, variables, config)
    if config.use_global_nooverlap:
        add_non_overlap_constraints_global(model, items, is_in, variables, geometry.separator)
    else:
        add_non_overlap_constraints(model, items, variables, geometry.separator)
    add_weight_constraints(model, items, is_in, variables)
    add_bin_height_constraints(model, items, is_in, variables)
    add_area_constraints(model, items, is_in, variables)
    bin_in_cabinet = add_cabinet_constraints(model, items, variables, geometry)
    if config.use_global_nooverlap:
        add_cabinet_z_nooverlap_global(model, bin_in_cabinet, variables, geometry)
    else:
        add_cabinet_z_nooverlap(model, variables, geometry)
    visibility_deviation = add_visibility_constraints(model, fam_in_bin, variables, geometry, visible_families or [], config)
    heavy_z = add_heavy_item_constraints(model, items, variables, geometry)
    family_cabinet_span, family_height_span = add_family_proximity_objective_terms(model, families, fam_in_bin, variables, geometry, config)

    build_objective(
        model,
        families,
        variables,
        family_drawer_count,
        xspan,
        yspan,
        visibility_deviation,
        heavy_z,
        family_cabinet_span,
        family_height_span,
        config,
    )

    return model, variables
