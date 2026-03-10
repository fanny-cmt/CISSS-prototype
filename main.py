from src.model import Item, SolverConfig
from src.solver import solve_2d_bins_fast
from src.visualization import plot_bins


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
        Item(id=0, family=0, w=18, d=12),
        Item(id=1, family=0, w=22, d=14),
        Item(id=2, family=0, w=26, d=18),
        Item(id=3, family=0, w=20, d=16),

        Item(id=4, family=1, w=44, d=12),
        Item(id=5, family=1, w=48, d=14),
        Item(id=6, family=1, w=30, d=16),

        Item(id=7, family=2, w=24, d=18),
        Item(id=8, family=2, w=26, d=20),
        Item(id=9, family=2, w=28, d=22),
        Item(id=10, family=2, w=36, d=24),

        Item(id=11, family=3, w=30, d=20),
        Item(id=12, family=3, w=24, d=18),
        Item(id=13, family=3, w=32, d=22),

        Item(id=14, family=4, w=28, d=16),
        Item(id=15, family=4, w=26, d=18),
        Item(id=16, family=4, w=30, d=20),

        Item(id=17, family=5, w=22, d=14),
        Item(id=18, family=5, w=24, d=16),
        Item(id=19, family=5, w=20, d=12),

        Item(id=20, family=6, w=24, d=18),
        Item(id=21, family=6, w=26, d=20),
        Item(id=22, family=6, w=28, d=22),
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
        config=SolverConfig(time_limit=30, num_workers=8),
    )

    print("Nombre minimal de bacs:", result.objective)

    plot_bins(result)
