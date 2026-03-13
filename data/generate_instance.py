"""
Générateur d'instances pour le problème de rangement en armoires médicales.

Usage:
    python generate_instance.py -o instance_big.json
    python generate_instance.py --items 1200 --families 25 --visible 8 --seed 123 -o mon_instance.json
    python generate_instance.py --items 200 --families 10 --heavy-ratio 0.05 -o petite.json
"""

import argparse
import json
import os
import random

# ── Constantes fixes (géométrie et types de bacs) ──────────────────────────

GEOMETRY = {
    "cabinet_height": 180,
    "separator": 1,
    "drawer_gap": 3,
    "eye_level": 140,
}

BIN_TYPES = [
    {"W": 70, "D": 50, "H": 15, "max_weight": 2500},
    {"W": 70, "D": 50, "H": 19, "max_weight": 2500},
    {"W": 70, "D": 50, "H": 28, "max_weight": 2500},
]

# ── Catalogue de familles disponibles ───────────────────────────────────────
# Chaque entrée : (nom, profil dimensionnel (w, d, h), peut_avoir_lourds)

FAMILY_CATALOG = [
    # Dimensions légèrement réduites vs original (~15-20%) pour tenir dans 1 tiroir
    ("Pansements",                  ((12, 24), (8, 18),  (6, 14)),  False),
    ("Gants",                       ((22, 34), (10, 18), (8, 14)),  True),
    ("Injection / perfusion",       ((18, 28), (12, 20), (10, 18)), True),
    ("Instruments stériles",        ((20, 32), (14, 22), (10, 18)), False),
    ("Dispositifs médicaux",        ((18, 30), (12, 20), (10, 18)), False),
    ("Désinfection",                ((16, 24), (10, 18), (8, 14)),  False),
    ("Prélèvements",                ((16, 26), (12, 20), (10, 18)), False),
    ("Compresses et gazes",         ((14, 26), (10, 20), (6, 16)),  False),
    ("Sondes et cathéters",         ((28, 42), (6, 14),  (6, 12)),  False),
    ("Protection individuelle",     ((20, 34), (14, 24), (12, 20)), True),
    ("Matériel de suture",          ((12, 24), (8, 18),  (6, 14)),  False),
    ("Oxygénothérapie",             ((22, 34), (12, 22), (10, 18)), True),
    ("Hygiène des mains",           ((14, 22), (8, 16),  (6, 12)),  False),
    ("Drainage",                    ((26, 40), (8, 16),  (6, 14)),  True),
    ("Poches et collecteurs",       ((18, 30), (14, 22), (12, 18)), False),
    ("Matériel d'incontinence",     ((20, 34), (16, 24), (12, 20)), True),
    ("Nutrition entérale",          ((24, 36), (12, 20), (10, 18)), True),
    ("Thermomètres et diagnostics", ((12, 20), (8, 16),  (6, 12)),  False),
    ("Immobilisation",              ((26, 40), (14, 24), (12, 20)), True),
    ("Matériel de pansement avancé",((14, 26), (10, 20), (8, 16)),  False),
    ("Électrodes et capteurs",      ((10, 20), (8, 16),  (4, 10)),  False),
    ("Tubulures",                   ((28, 42), (6, 12),  (4, 10)),  False),
    ("Stomathérapie",               ((18, 30), (12, 20), (8, 18)),  True),
    ("Matériel de réanimation",     ((24, 38), (16, 26), (14, 22)), True),
    ("Aiguilles et lames",          ((8, 18),  (6, 12),  (4, 8)),   False),
    ("Sparadraps et adhésifs",      ((12, 22), (8, 16),  (6, 12)),  False),
    ("Conteneurs DASRI",            ((20, 34), (18, 28), (16, 24)), True),
    ("Protections cutanées",        ((14, 24), (10, 18), (6, 14)),  False),
    ("Sets de soins",               ((18, 32), (14, 22), (10, 18)), False),
    ("Matériel ophtalmique",        ((10, 18), (6, 14),  (4, 10)),  False),
]


def round_even(x):
    """Arrondir au nombre pair supérieur ou égal."""
    return x if x % 2 == 0 else x + 1


def generate_variants(w, d, h):
    """Génère 3-8 variantes cohérentes (permutations d'orientation)."""
    all_perms = [
        (w, d, h), (w, h, d),
        (d, w, h), (d, h, w),
        (h, w, d), (h, d, w),
    ]
    seen = set()
    unique = []
    for p in all_perms:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    # Si trop peu de permutations uniques (dims égales), ajouter des tweaks ±2
    if len(unique) < 3:
        for p in list(unique):
            for delta in [2, -2]:
                for axis in range(3):
                    candidate = list(p)
                    candidate[axis] += delta
                    candidate = tuple(candidate)
                    if candidate not in seen and all(v > 0 for v in candidate):
                        unique.append(candidate)
                        seen.add(candidate)
                    if len(unique) >= 8:
                        break

    num_variants = random.randint(3, min(8, max(3, len(unique))))

    chosen = [(w, d, h)]
    rest = [v for v in unique if v != (w, d, h)]
    random.shuffle(rest)
    chosen.extend(rest[: num_variants - 1])

    return [{"w": v[0], "d": v[1], "h": v[2]} for v in chosen]


def distribute_items(n_items, n_families):
    """Répartit n_items sur n_families de manière à peu près uniforme avec variation."""
    base = n_items // n_families
    margin = max(1, base // 4)
    sizes = []
    remaining = n_items
    for i in range(n_families):
        if i == n_families - 1:
            sizes.append(remaining)
        else:
            lo = max(1, base - margin)
            hi = base + margin
            hi = min(hi, remaining - (n_families - i - 1) * max(1, base - margin))
            lo = min(lo, hi)
            size = random.randint(lo, hi)
            sizes.append(size)
            remaining -= size
    return sizes


def generate_instance(n_items, n_families, n_visible, heavy_ratio, seed):
    random.seed(seed)

    # Sélectionner les familles depuis le catalogue (cyclique si n_families > catalogue)
    selected = []
    for i in range(n_families):
        selected.append(FAMILY_CATALOG[i % len(FAMILY_CATALOG)])

    family_names = {str(i): selected[i][0] for i in range(n_families)}
    dim_profiles = {i: selected[i][1] for i in range(n_families)}
    can_be_heavy = {i for i in range(n_families) if selected[i][2]}

    # Choisir les familles visibles parmi celles sans objets lourds
    non_heavy_families = [i for i in range(n_families) if i not in can_be_heavy]
    n_visible = min(n_visible, len(non_heavy_families))
    visible_families = sorted(random.sample(non_heavy_families, n_visible))

    # Répartition des items
    family_sizes = distribute_items(n_items, n_families)

    # Proportion d'objets lourds par famille pouvant en avoir
    # On ajuste pour atteindre heavy_ratio globalement
    n_heavy_target = int(n_items * heavy_ratio)
    heavy_pool_size = sum(family_sizes[i] for i in can_be_heavy)
    heavy_prob = n_heavy_target / heavy_pool_size if heavy_pool_size > 0 else 0
    heavy_prob = min(heavy_prob, 0.5)  # cap

    items = []
    item_id = 0

    for family in range(n_families):
        count = family_sizes[family]
        profile = dim_profiles[family]
        has_heavy = family in can_be_heavy

        for _ in range(count):
            w = round_even(random.randint(profile[0][0], profile[0][1]))
            d = round_even(random.randint(profile[1][0], profile[1][1]))
            h = round_even(random.randint(profile[2][0], profile[2][1]))

            vol = w * d * h
            base_weight = int(vol * 0.08 + random.randint(50, 150))

            heavy = False
            if has_heavy and random.random() < heavy_prob:
                base_weight = random.randint(400, 580)
                heavy = True
            else:
                base_weight = max(100, min(base_weight, 390))

            variants = generate_variants(w, d, h)

            items.append({
                "id": item_id,
                "family": family,
                "weight": base_weight,
                "heavy": heavy,
                "variants": variants,
            })
            item_id += 1

    return {
        "geometry": GEOMETRY,
        "visible_families": visible_families,
        "family_names": family_names,
        "bin_types": BIN_TYPES,
        "items": items,
    }


def print_stats(instance):
    items = instance["items"]
    n = len(items)
    heavy_count = sum(1 for it in items if it["heavy"])
    families = instance["family_names"]

    from collections import Counter
    fam_counts = Counter(it["family"] for it in items)

    print(f"Total items:       {n}")
    print(f"Familles:          {len(families)}")
    print(f"Heavy items:       {heavy_count} ({heavy_count / n * 100:.1f}%)")
    print(f"Visible families:  {instance['visible_families']}")
    print(f"Items par famille: {dict(sorted(fam_counts.items()))}")

    # Vérification : aucune visible family ne contient d'objet lourd
    vis = set(instance["visible_families"])
    errors = [it for it in items if it["family"] in vis and it["heavy"]]
    if errors:
        print(f"ERREUR: {len(errors)} objet(s) lourd(s) dans des familles visibles!")
    else:
        print("OK: aucun objet lourd dans les familles visibles.")


def main():
    parser = argparse.ArgumentParser(
        description="Génère une instance JSON pour le problème de rangement en armoires médicales."
    )
    parser.add_argument("-o", "--output", required=True,
                        help="Chemin du fichier JSON de sortie")
    parser.add_argument("--items", type=int, default=800,
                        help="Nombre total d'items (défaut: 800)")
    parser.add_argument("--families", type=int, default=20,
                        help="Nombre de familles (défaut: 20)")
    parser.add_argument("--visible", type=int, default=6,
                        help="Nombre de familles visibles (défaut: 6)")
    parser.add_argument("--heavy-ratio", type=float, default=0.10,
                        help="Proportion d'objets lourds (défaut: 0.10)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Seed aléatoire (défaut: 42)")

    args = parser.parse_args()

    instance = generate_instance(
        n_items=args.items,
        n_families=args.families,
        n_visible=args.visible,
        heavy_ratio=args.heavy_ratio,
        seed=args.seed,
    )

    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(os.path.dirname(__file__), output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(instance, f, indent=2, ensure_ascii=False)

    print_stats(instance)
    print(f"\nÉcrit dans {output_path}")


if __name__ == "__main__":
    main()
