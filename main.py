from src.types import SolverConfig
from src.loader import load_instance
from src.solver import solve_2d_bins_fast
from src.visualization import plot_bins, plot_cabinets


if __name__ == "__main__":
    instance = load_instance("data/instance.json")

    result = solve_2d_bins_fast(
        items=instance["items"],
        families=instance["families"],
        bin_types=instance["bin_types"],
        geometry=instance["geometry"],
        config=SolverConfig(),
    )

    print(f"Bins: {result.num_bins}, Armoires: {result.num_cabinets}")

    plot_cabinets(result, instance["geometry"])
    plot_bins(result)
