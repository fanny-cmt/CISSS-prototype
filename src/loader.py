import json
from pathlib import Path

from src.types import Item, Variant, BinType


def load_instance(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    family_names = {int(k): v for k, v in data["family_names"].items()}

    bin_types = [
        BinType(W=bt["W"], D=bt["D"], max_weight=bt["max_weight"])
        for bt in data["bin_types"]
    ]

    items = [
        Item(
            id=it["id"],
            family=it["family"],
            weight=it["weight"],
            variants=[Variant(w=v["w"], d=v["d"]) for v in it["variants"]],
        )
        for it in data["items"]
    ]

    families = sorted(family_names.keys())

    return {
        "family_names": family_names,
        "families": families,
        "bin_types": bin_types,
        "items": items,
    }
