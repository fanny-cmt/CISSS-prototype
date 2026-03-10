from src.types import Item, Variant, SolverConfig
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
        Item(id=0, family=0, variants=[Variant(18,12), Variant(12,18), Variant(20,10)]),
        Item(id=1, family=0, variants=[Variant(22,14), Variant(14,22), Variant(24,12)]),
        Item(id=2, family=0, variants=[Variant(26,18), Variant(18,26), Variant(28,16)]),
        Item(id=3, family=0, variants=[Variant(20,16), Variant(16,20), Variant(22,14)]),

        Item(id=4, family=1, variants=[Variant(44,12), Variant(12,44), Variant(46,10)]),
        Item(id=5, family=1, variants=[Variant(48,14), Variant(14,48), Variant(50,12)]),
        Item(id=6, family=1, variants=[Variant(30,16), Variant(16,30), Variant(32,14)]),

        Item(id=7, family=2, variants=[Variant(24,18), Variant(18,24), Variant(26,16)]),
        Item(id=8, family=2, variants=[Variant(26,20), Variant(20,26), Variant(28,18)]),
        Item(id=9, family=2, variants=[Variant(28,22), Variant(22,28), Variant(30,20)]),
        Item(id=10, family=2, variants=[Variant(36,24), Variant(24,36), Variant(38,22)]),

        Item(id=11, family=3, variants=[Variant(30,20), Variant(20,30), Variant(32,18)]),
        Item(id=12, family=3, variants=[Variant(24,18), Variant(18,24), Variant(26,16)]),
        Item(id=13, family=3, variants=[Variant(32,22), Variant(22,32), Variant(34,20)]),

        Item(id=14, family=4, variants=[Variant(28,16), Variant(16,28), Variant(30,14)]),
        Item(id=15, family=4, variants=[Variant(26,18), Variant(18,26), Variant(28,16)]),
        Item(id=16, family=4, variants=[Variant(30,20), Variant(20,30), Variant(32,18)]),

        Item(id=17, family=5, variants=[Variant(22,14), Variant(14,22), Variant(24,12)]),
        Item(id=18, family=5, variants=[Variant(24,16), Variant(16,24), Variant(26,14)]),
        Item(id=19, family=5, variants=[Variant(20,12), Variant(12,20), Variant(22,10)]),

        Item(id=20, family=6, variants=[Variant(24,18), Variant(18,24), Variant(26,16)]),
        Item(id=21, family=6, variants=[Variant(26,20), Variant(20,26), Variant(28,18)]),
        Item(id=22, family=6, variants=[Variant(28,22), Variant(22,28), Variant(30,20)]),
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
