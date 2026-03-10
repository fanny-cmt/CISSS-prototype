import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
from collections import defaultdict

from src.types import Geometry, Solution


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
        ax.set_title(f"Tiroir {b.bin_id} (type {b.type}) H={b.H}cm — épaisseur={b.occupied_H}cm\nArmoire {b.cabinet} Z={b.Z}cm — {total_weight}g")
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


def plot_cabinets(solution: Solution, geometry: Geometry) -> None:
    bins = solution.bins

    if not bins:
        print("Aucune armoire à afficher.")
        return

    cabinet_height = geometry.cabinet_height

    # Group bins by cabinet
    cabinets: dict[int, list] = defaultdict(list)
    for b in bins:
        cabinets[b.cabinet].append(b)

    num_cabinets = len(cabinets)
    cabinet_ids = sorted(cabinets.keys())

    # Color bins by type
    all_types = sorted({b.type for b in bins})
    type_cmap = cm.get_cmap("Set2", max(len(all_types), 1))
    type_colors = {t: type_cmap(i) for i, t in enumerate(all_types)}

    fig, axes = plt.subplots(1, num_cabinets, figsize=(5 * num_cabinets, 8))

    if num_cabinets == 1:
        axes = [axes]

    drawer_width = 60  # visual width for the cabinet front view

    for ax, cab_id in zip(axes, cabinet_ids):
        cab_bins = cabinets[cab_id]
        total_weight = sum(item.weight for b in cab_bins for item in b.items)

        ax.set_title(f"Armoire {cab_id}\n{len(cab_bins)} tiroirs — {total_weight}g")
        ax.set_xlim(-5, drawer_width + 5)
        ax.set_ylim(-5, cabinet_height + 5)
        ax.set_aspect("equal")

        # Cabinet frame
        frame = patches.Rectangle(
            (0, 0),
            drawer_width,
            cabinet_height,
            linewidth=2.5,
            edgecolor="black",
            facecolor="#f5f5f0",
        )
        ax.add_patch(frame)

        # Draw each bin as a horizontal band
        for b in cab_bins:
            color = type_colors.get(b.type, "#cccccc")

            # Bin nominal height (lighter background)
            nominal = patches.Rectangle(
                (1, b.Z),
                drawer_width - 2,
                b.H,
                linewidth=1,
                edgecolor="grey",
                facecolor=color,
                alpha=0.3,
            )
            ax.add_patch(nominal)

            # Occupied height (solid)
            occupied = patches.Rectangle(
                (1, b.Z),
                drawer_width - 2,
                b.occupied_H,
                linewidth=1.5,
                edgecolor="black",
                facecolor=color,
                alpha=0.6,
            )
            ax.add_patch(occupied)

            # Overflow indicator: dashed line at nominal height if occupied > H
            if b.occupied_H > b.H:
                ax.plot(
                    [1, drawer_width - 1],
                    [b.Z + b.H, b.Z + b.H],
                    linestyle="--",
                    color="red",
                    linewidth=1,
                )

            # Label inside the bin
            label_y = b.Z + b.occupied_H / 2
            ax.text(
                drawer_width / 2,
                label_y,
                f"Tiroir {b.bin_id} (type {b.type})\nH={b.H} occ={b.occupied_H}\nZ={b.Z}",
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
            )

        ax.set_xlabel("vue de face (cm)")
        ax.set_ylabel("hauteur (cm)")
        ax.set_yticks(range(0, cabinet_height + 1, 10))
        ax.grid(axis="y", linestyle=":", alpha=0.4)

    fig.suptitle("Placement des tiroirs dans les armoires", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.show()
