from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import random

def solve_2d_bins_fast(items, bin_types, separator=1, time_limit=60, num_workers=8):
    indexed_items = list(enumerate(items))
    indexed_items.sort(key=lambda p: p[1][0] * p[1][1], reverse=True)

    original_ids = [idx for idx, _ in indexed_items]
    items = [dims for _, dims in indexed_items]

    n = len(items)
    T = len(bin_types)

    max_W = max(W for W, H in bin_types)
    max_H = max(H for W, H in bin_types)

    for i, (w, h) in enumerate(items):
        if all(w > W or h > H for W, H in bin_types):
            raise ValueError(f"Objet impossible à placer: {(w, h)}")

    model = cp_model.CpModel()

    num_bins = model.new_int_var(1, n, "num_bins")

    bin_of = [model.new_int_var(0, i, f"bin_of[{i}]") for i in range(n)]
    x = [model.new_int_var(0, max_W, f"x[{i}]") for i in range(n)]
    y = [model.new_int_var(0, max_H, f"y[{i}]") for i in range(n)]

    bin_type = [model.new_int_var(0, T - 1, f"bin_type[{k}]") for k in range(n)]

    W_values = [W for W, H in bin_types]
    H_values = [H for W, H in bin_types]

    W_of_bin = [model.new_int_var(min(W_values), max(W_values), f"W_of_bin[{k}]") for k in range(n)]
    H_of_bin = [model.new_int_var(min(H_values), max(H_values), f"H_of_bin[{k}]") for k in range(n)]

    for k in range(n):
        model.add_element(bin_type[k], W_values, W_of_bin[k])
        model.add_element(bin_type[k], H_values, H_of_bin[k])

    model.add(bin_of[0] == 0)
    for i in range(n):
        model.add(bin_of[i] < num_bins)

    # L'objet i doit tenir dans le bac qu'il utilise
    for i, (w, h) in enumerate(items):
        for k in range(i + 1):  # domaine de bin_of[i]
            is_in_k = model.new_bool_var(f"is_in[{i},{k}]")
            model.add(bin_of[i] == k).only_enforce_if(is_in_k)
            model.add(bin_of[i] != k).only_enforce_if(is_in_k.Not())

            model.add(x[i] + w <= W_of_bin[k]).only_enforce_if(is_in_k)
            model.add(y[i] + h <= H_of_bin[k]).only_enforce_if(is_in_k)

    # Non-chevauchement
    for i in range(n):
        wi, hi = items[i]
        for j in range(i + 1, n):
            wj, hj = items[j]

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
            model.add(y[i] + hi + separator <= y[j]).only_enforce_if(below_ij)
            model.add(y[j] + hj + separator <= y[i]).only_enforce_if(below_ji)

            model.add_implication(left_ij, same_bin)
            model.add_implication(left_ji, same_bin)
            model.add_implication(below_ij, same_bin)
            model.add_implication(below_ji, same_bin)

    model.minimize(num_bins)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = num_workers
    solver.parameters.symmetry_level = 2

    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": solver.status_name(status), "objective": None, "bins": []}

    bins = {}
    for i, (w, h) in enumerate(items):
        k = solver.value(bin_of[i])
        if k not in bins:
            t = solver.value(bin_type[k])
            bins[k] = {
                "bin_id": k,
                "type": t,
                "W": solver.value(W_of_bin[k]),
                "H": solver.value(H_of_bin[k]),
                "items": [],
            }
        bins[k]["items"].append({
            "item": original_ids[i],
            "w": w,
            "h": h,
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

    for ax, b in zip(axes, bins):

        W = b["W"]
        H = b["H"]

        ax.set_title(f"Bac {b['bin_id']} (type {b['type']})")
        ax.set_xlim(0, W)
        ax.set_ylim(0, H)
        ax.set_aspect("equal")

        # contour du bac
        rect = patches.Rectangle(
            (0, 0), W, H,
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
            h = item["h"]

            color = (random.random(), random.random(), random.random())

            rect = patches.Rectangle(
                (x, y),
                w,
                h,
                linewidth=1,
                edgecolor="black",
                facecolor=color,
                alpha=0.6
            )

            ax.add_patch(rect)

            ax.text(
                x + w / 2,
                y + h / 2,
                f"{item['item']}",
                ha="center",
                va="center",
                fontsize=10
            )

        ax.set_xlabel("X")
        ax.set_ylabel("Y")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Exemple
    items = [

        # compresses stériles
        (40, 10),

        # boîtes de gants
        (44, 12),

        # seringues
        (18, 24),

        # pansements
        (15, 30),

        # sets de perfusion
        (25, 36),

        # kits de sutures
        (20, 30),

        # champs stériles pliés
        (30, 40),

        # sondes
        (28, 16),

        # packs divers
        (12, 32),

        # petits instruments
        (16, 20),

    ]
    # 3 types de bacs
    bin_types = [
        (40, 30),   # petit tiroir
        (60, 40),   # tiroir moyen
        (80, 60)    # grand tiroir
    ]

    result = solve_2d_bins_fast(
        items=items,
        bin_types=bin_types,
        time_limit=30,
        num_workers=8,
    )

    print("Nombre minimal de bacs:", result["objective"])

    plot_bins(result)

