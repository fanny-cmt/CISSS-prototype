import json
from pathlib import Path

from src.types import Item, Variant, BinType, Geometry


def load_instance(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    family_names = {int(k): v for k, v in data["family_names"].items()}

    bin_types = [
        BinType(W=bt["W"], D=bt["D"], H=bt["H"], max_weight=bt["max_weight"])
        for bt in data["bin_types"]
    ]

    items = [
        Item(
            id=it["id"],
            family=it["family"],
            weight=it["weight"],
            variants=[Variant(w=v["w"], d=v["d"], h=v["h"]) for v in it["variants"]],
            heavy=it["heavy"],
        )
        for it in data["items"]
    ]

    families = sorted(family_names.keys())

    geo = data["geometry"]
    geometry = Geometry(cabinet_height=geo["cabinet_height"], separator=geo["separator"], drawer_gap=geo["drawer_gap"], eye_level=geo["eye_level"])

    visible_families = data.get("visible_families", [])

    return {
        "family_names": family_names,
        "families": families,
        "bin_types": bin_types,
        "items": items,
        "geometry": geometry,
        "visible_families": visible_families,
    }
