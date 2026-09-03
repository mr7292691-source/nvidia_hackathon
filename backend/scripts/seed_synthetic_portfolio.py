"""
Regenerates app/evidence/adapters/replay/synthetic_portfolio.json with a
larger set of de-identified synthetic policies scattered around the demo
event's bbox. Run manually when the team wants a richer demo dataset than
the 3-policy sample checked in by default.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "app" / "evidence" / "adapters" / "replay" / "synthetic_portfolio.json"

# Demo bbox from app/api/routes/replay.py
BBOX = {"lon_min": -95.55, "lon_max": -95.30, "lat_min": 29.60, "lat_max": 29.85}

OCCUPANCIES = ["single_family_residential", "commercial_retail", "multi_family_residential"]


def gen_policy(i: int) -> dict:
    lon = random.uniform(BBOX["lon_min"], BBOX["lon_max"])
    lat = random.uniform(BBOX["lat_min"], BBOX["lat_max"])
    tiv = random.choice([250_000, 450_000, 800_000, 1_200_000, 2_000_000])
    limit = int(tiv * random.choice([0.8, 1.0]))
    deductible = random.choice([2_500, 5_000, 10_000, 25_000])
    return {
        "policy_id": f"SYN-POL-{10000 + i}",
        "location": {"type": "Point", "coordinates": [round(lon, 4), round(lat, 4)]},
        "tiv_usd": tiv,
        "limit_usd": limit,
        "deductible_usd": deductible,
        "occupancy": random.choice(OCCUPANCIES),
    }


def main(n: int = 25) -> None:
    policies = [gen_policy(i) for i in range(1, n + 1)]
    OUTPUT.write_text(json.dumps(policies, indent=2))
    print(f"Wrote {n} synthetic policies to {OUTPUT}")


if __name__ == "__main__":
    main()
