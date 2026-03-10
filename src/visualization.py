import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm

from src.types import Solution


def plot_bins(solution: Solution) -> None:
    bins = solution.bins

    if not bins:
        print("Aucun bac à afficher.")
        return

    nb = len(bins)

    fig, axes = plt.subplots(1, nb, figsize=(6 * nb, 6))

    if nb == 1:
        axes = [axes]

    # Collect all family IDs and assign colors dynamically
    all_families = sorted({item.family for b in bins for item in b.items})
    colormap = cm.get_cmap("tab10", max(len(all_families), 1))
    family_colors = {f: colormap(i) for i, f in enumerate(all_families)}

    for ax, b in zip(axes, bins):

        W = b.W
        D = b.D

        total_weight = sum(item.weight for item in b.items)
        ax.set_title(f"Tiroir {b.bin_id} (type {b.type}) H={b.H}cm\nArmoire {b.cabinet} Z={b.Z}cm — {total_weight}g")
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
        for item in b.items:

            color = family_colors.get(item.family, "#cccccc")

            rect = patches.Rectangle(
                (item.x, item.y),
                item.w,
                item.d,
                linewidth=1,
                edgecolor="black",
                facecolor=color,
                alpha=0.7
            )

            ax.add_patch(rect)

            ax.text(
                item.x + item.w / 2,
                item.y + item.d / 2,
                f"{item.item}\nF{item.family} V{item.variant}\n{item.weight}g h={item.h}",
                ha="center",
                va="center",
                fontsize=8
            )

        ax.set_xlabel("largeur (cm)")
        ax.set_ylabel("profondeur (cm)")

    plt.tight_layout()
    plt.show()
