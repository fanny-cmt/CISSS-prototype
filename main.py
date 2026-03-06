from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def solve_2d_bins_fast(items, families, bin_types, separator=1, time_limit=60, num_workers=8):
    indexed_items = list(enumerate(items))
    indexed_items.sort(key=lambda p: (p[1]["family"], -(p[1]["w"] * p[1]["d"])))

    original_ids = [idx for idx, _ in indexed_items]
    items = [dims for _, dims in indexed_items]

    n = len(items)
    T = len(bin_types)

    max_W = max(W for W, _ in bin_types)
    max_D = max(D for _, D in bin_types)

    for i, item in enumerate(items):
        w = item["w"]
        d = item["d"]
        if all(w > W or d > D for W, D in bin_types):
            raise ValueError(f"Objet impossible à placer: {(w, d)}")

    model = cp_model.CpModel()

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

    fam_in_bin = {}

    for f in families:
        for k in range(n):
            fam_in_bin[f, k] = model.new_bool_var(f"fam_{f}_in_bin_{k}")

    model.add(bin_of[0] == 0)
    for i in range(n):
        model.add(bin_of[i] < num_bins)

    # L'objet i doit tenir dans le bac qu'il utilise
    is_in = {}
    
    for i, item in enumerate(items):
        w = item["w"]
        d = item["d"]
        for k in range(i + 1):  # domaine de bin_of[i]
            is_in[i, k] = model.new_bool_var(f"is_in[{i},{k}]")
            model.add(bin_of[i] == k).only_enforce_if(is_in[i, k])
            model.add(bin_of[i] != k).only_enforce_if(is_in[i, k].Not())

            model.add(x[i] + w <= W_of_bin[k]).only_enforce_if(is_in[i, k])
            model.add(y[i] + d <= D_of_bin[k]).only_enforce_if(is_in[i, k])

    for i, item in enumerate(items):
        f = item["family"]
        for k in range(i + 1):
            model.add_implication(is_in[i, k], fam_in_bin[f, k])

    for f in families:
        items_f = [i for i,item in enumerate(items) if item["family"] == f]

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
        f = item["family"]
        w = item["w"]
        d = item["d"]

        for k in range(i + 1):
            model.add(xmin[f, k] <= x[i]).only_enforce_if(is_in[i, k])
            model.add(xmax[f, k] >= x[i] + w).only_enforce_if(is_in[i, k])
            model.add(ymin[f, k] <= y[i]).only_enforce_if(is_in[i, k])
            model.add(ymax[f, k] >= y[i] + d).only_enforce_if(is_in[i, k])

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

    # Non-chevauchement
    for i in range(n):
        item = items[i]
        wi = item["w"]
        di = item["d"]
        for j in range(i + 1, n):
            item2 = items[j]
            wj = item2["w"]
            dj = item2["d"]

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

    model.minimize(1000*num_bins 
                   + 10*sum(family_drawer_count[f] for f in families)
                   + sum(xspan[f, k] + yspan[f, k] for f in families for k in range(n)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = num_workers
    solver.parameters.symmetry_level = 2

    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": solver.status_name(status), "objective": None, "bins": []}

    bins = {}
    for i, item in enumerate(items):
        w = item["w"]
        d = item["d"]
        family = item["family"]
        k = solver.value(bin_of[i])
        if k not in bins:
            t = solver.value(bin_type[k])
            bins[k] = {
                "bin_id": k,
                "type": t,
                "W": solver.value(W_of_bin[k]),
                "D": solver.value(D_of_bin[k]),
                "items": [],
            }
        bins[k]["items"].append({
            "item": original_ids[i],
            "family": family,
            "w": w,
            "d": d,
            "x": solver.value(x[i]),
            "y": solver.value(y[i]),
        })

    return {
        "status": solver.status_name(status),
        "objective": solver.value(num_bins),
        "bins": [bins[k] for k in sorted(bins)],
    }

def plot_bins(solution):
    """
    solution : dictionnaire retourné par solve_2d_multi_bin_packing_cp_sat
    """

    bins = solution["bins"]

    if not bins:
        print("Aucun bac à afficher.")
        return

    nb = len(bins)

    fig, axes = plt.subplots(1, nb, figsize=(6 * nb, 6))

    if nb == 1:
        axes = [axes]

    # Couleurs fixes par famille
    family_colors = {
        0: "#f4a6a6",
        1: "#a6d3f4",
        2: "#a6f4c5",
        3: "#f4d7a6",
        4: "#c9a6f4",
        5: "#f4a6e1",
        6: "#b6f4a6",
    }

    default_color = "#cccccc"

    for ax, b in zip(axes, bins):

        W = b["W"]
        D = b["D"]

        ax.set_title(f"Tiroir {b['bin_id']} (type {b['type']})")
        ax.set_xlim(0, W)
        ax.set_ylim(0, D)
        ax.set_aspect("equal")

        # contour du tiroir
        rect = patches.Rectangle(
            (0, 0),
            W,
            D,
            linewidth=2,
            edgecolor="black",
            facecolor="none"
        )
        ax.add_patch(rect)

        # objets
        for item in b["items"]:

            x = item["x"]
            y = item["y"]
            w = item["w"]
            d = item["d"]
            family = item.get("family", -1)

            color = family_colors.get(family, default_color)

            rect = patches.Rectangle(
                (x, y),
                w,
                d,
                linewidth=1,
                edgecolor="black",
                facecolor=color,
                alpha=0.7
            )

            ax.add_patch(rect)

            ax.text(
                x + w / 2,
                y + d / 2,
                f"{item['item']}\nF{family}",
                ha="center",
                va="center",
                fontsize=9
            )

        ax.set_xlabel("largeur (cm)")
        ax.set_ylabel("profondeur (cm)")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Exemple
    family_names = {
    0: "Pansements",
    1: "Gants",
    2: "Injection / perfusion",
    3: "Instruments stériles",
    4: "Dispositifs médicaux",
    5: "Désinfection",
    6: "Prélèvements",
    }

    families = range(7)

    items = [

        {"id": 0, "family": 0, "w": 18, "d": 12},
        {"id": 1, "family": 0, "w": 22, "d": 14},
        {"id": 2, "family": 0, "w": 26, "d": 18},
        {"id": 3, "family": 0, "w": 20, "d": 16},

        {"id": 4, "family": 1, "w": 44, "d": 12},
        {"id": 5, "family": 1, "w": 48, "d": 14},
        {"id": 6, "family": 1, "w": 30, "d": 16},

        {"id": 7, "family": 2, "w": 24, "d": 18},
        {"id": 8, "family": 2, "w": 26, "d": 20},
        {"id": 9, "family": 2, "w": 28, "d": 22},
        {"id": 10, "family": 2, "w": 36, "d": 24},

        {"id": 11, "family": 3, "w": 30, "d": 20},
        {"id": 12, "family": 3, "w": 24, "d": 18},
        {"id": 13, "family": 3, "w": 32, "d": 22},

        {"id": 14, "family": 4, "w": 28, "d": 16},
        {"id": 15, "family": 4, "w": 26, "d": 18},
        {"id": 16, "family": 4, "w": 30, "d": 20},

        {"id": 17, "family": 5, "w": 22, "d": 14},
        {"id": 18, "family": 5, "w": 24, "d": 16},
        {"id": 19, "family": 5, "w": 20, "d": 12},

        {"id": 20, "family": 6, "w": 24, "d": 18},
        {"id": 21, "family": 6, "w": 26, "d": 20},
        {"id": 22, "family": 6, "w": 28, "d": 22},

    ]

    # 3 types de bacs
    bin_types = [
        (40, 30),   # petit tiroir
        (60, 40),   # tiroir moyen
        (80, 60)    # grand tiroir
    ]

    result = solve_2d_bins_fast(
        items=items,
        families=families,
        bin_types=bin_types,
        time_limit=30,
        num_workers=8,
    )

    print("Nombre minimal de bacs:", result["objective"])

    plot_bins(result)

