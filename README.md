# CISSS — Optimisation du rangement en armoires

Outil d'optimisation pour le placement d'articles médicaux dans des tiroirs et armoires, utilisant la programmation par contraintes (CP-SAT de Google OR-Tools).

## Problème

Étant donné un ensemble d'articles (avec familles, poids, dimensions, variantes d'orientation) et des types de tiroirs disponibles, le solveur cherche à :

- **Minimiser** le nombre d'armoires et de tiroirs utilisés
- **Regrouper** les articles d'une même famille dans un minimum de tiroirs
- **Respecter** les contraintes de non-chevauchement 2D, de poids max par tiroir, de hauteur, et de capacité des armoires
- **Placer** les articles lourds (`heavy`) le plus bas possible dans les armoires
- **Rapprocher** les familles visibles (`visible_families`) du niveau des yeux

## Structure du projet

```
├── main.py                  # Point d'entrée
├── data/
│   ├── instance.json        # Instance de test
│   └── instance_large.json  # Instance plus grande
├── src/
│   ├── types.py             # Structures de données (Item, BinType, Geometry, Solution, ...)
│   ├── loader.py            # Chargement d'une instance JSON
│   ├── heuristic.py         # Heuristique gloutonne pour les bornes supérieures
│   ├── model.py             # Construction du modèle CP-SAT (variables, contraintes, objectif)
│   ├── solver.py            # Résolution et extraction de la solution
│   └── visualization.py     # Visualisation matplotlib (vue tiroirs + vue armoires)
└── pyproject.toml
```

## Installation

Nécessite Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install ortools matplotlib
```

## Utilisation

```bash
python main.py
```

Le programme charge l'instance depuis `data/instance.json`, résout le problème et affiche deux visualisations :

1. **Vue armoires** — placement vertical des tiroirs dans les armoires (avec indicateurs pour les familles visibles et articles lourds)
2. **Vue tiroirs** — placement 2D des articles dans chaque tiroir

## Format de l'instance JSON

```json
{
  "geometry": {
    "cabinet_height": 100,
    "separator": 1,
    "drawer_gap": 3,
    "eye_level": 70
  },
  "visible_families": [5],
  "family_names": { "0": "Pansements", "1": "Gants", ... },
  "bin_types": [
    { "W": 70, "D": 50, "H": 15, "max_weight": 2500 }
  ],
  "items": [
    {
      "id": 0,
      "family": 0,
      "weight": 150,
      "heavy": false,
      "variants": [
        { "w": 18, "d": 12, "h": 10 },
        { "w": 12, "d": 18, "h": 10 }
      ]
    }
  ]
}
```

## Configuration du solveur

Les paramètres sont ajustables via `SolverConfig` :

| Paramètre | Défaut | Description |
|---|---|---|
| `time_limit` | 60 | Temps max de résolution (secondes) |
| `num_workers` | 8 | Nombre de threads de recherche |
| `cabinet_weight` | 100 000 | Poids dans l'objectif : nombre d'armoires |
| `bin_weight` | 100 | Poids dans l'objectif : nombre de tiroirs |
| `family_weight` | 1 000 | Poids dans l'objectif : dispersion des familles |
| `visibility_weight` | 1 | Poids dans l'objectif : distance au niveau des yeux |
| `heavy_weight` | 1 | Poids dans l'objectif : hauteur Z des articles lourds |

## Dépendances

- [OR-Tools](https://developers.google.com/optimization) — solveur CP-SAT
- [Matplotlib](https://matplotlib.org/) — visualisation
