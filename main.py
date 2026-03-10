from src.types import SolverConfig
from src.loader import load_instance
from src.solver import solve_2d_bins_fast
from src.visualization import plot_bins


if __name__ == "__main__":
    instance = load_instance("data/instance.json")

    result = solve_2d_bins_fast(
        items=instance["items"],
        families=instance["families"],
        bin_types=instance["bin_types"],
        config=SolverConfig(time_limit=30, num_workers=8),
    )

    print("Nombre minimal de bacs:", result.objective)

    plot_bins(result)
