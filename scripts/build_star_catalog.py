import json
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LOD_DIR = DATA_DIR / "stars-lod"


BRIGHT_STARS = [
    ("Sirius", 101.287, -16.716, 8.60, -1.46, "A1V"),
    ("Canopus", 95.988, -52.696, 310.0, -0.74, "A9II"),
    ("Alpha Centauri", 219.902, -60.834, 4.37, -0.27, "G2V/K1V"),
    ("Arcturus", 213.915, 19.182, 36.7, -0.05, "K1.5III"),
    ("Vega", 279.234, 38.784, 25.0, 0.03, "A0V"),
    ("Capella", 79.172, 45.998, 42.9, 0.08, "G8III"),
    ("Rigel", 78.634, -8.202, 860.0, 0.13, "B8Ia"),
    ("Procyon", 114.825, 5.225, 11.46, 0.34, "F5IV"),
    ("Betelgeuse", 88.793, 7.407, 548.0, 0.42, "M1Iab"),
    ("Achernar", 24.429, -57.237, 139.0, 0.46, "B6Vep"),
    ("Hadar", 210.956, -60.373, 390.0, 0.61, "B1III"),
    ("Altair", 297.696, 8.868, 16.7, 0.77, "A7V"),
    ("Acrux", 186.650, -63.099, 320.0, 0.76, "B0.5IV"),
    ("Aldebaran", 68.980, 16.509, 65.3, 0.85, "K5III"),
    ("Antares", 247.352, -26.432, 550.0, 1.06, "M1.5Iab"),
    ("Spica", 201.298, -11.161, 250.0, 0.98, "B1V"),
    ("Pollux", 116.329, 28.026, 33.8, 1.14, "K0III"),
    ("Fomalhaut", 344.413, -29.622, 25.1, 1.16, "A3V"),
    ("Deneb", 310.358, 45.280, 2615.0, 1.25, "A2Ia"),
    ("Mimosa", 191.930, -59.688, 280.0, 1.25, "B0.5III"),
    ("Regulus", 152.093, 11.967, 79.3, 1.35, "B8IV"),
    ("Adhara", 104.656, -28.972, 430.0, 1.50, "B2II"),
    ("Castor", 113.650, 31.888, 51.0, 1.58, "A1V"),
    ("Gacrux", 187.792, -57.113, 88.6, 1.63, "M3.5III"),
]


def spectral_color(spectral_type: str) -> str:
    first = spectral_type[:1].upper()
    return {
        "O": "#9bb8ff",
        "B": "#aabfff",
        "A": "#cad7ff",
        "F": "#f8f7ff",
        "G": "#fff4d8",
        "K": "#ffd2a1",
        "M": "#ffb07c",
    }.get(first, "#ffffff")


def radec_to_xyz(ra_deg: float, dec_deg: float, distance_ly: float, scale: float = 0.22) -> list[float]:
    ra = math.radians(ra_deg)
    dec = math.radians(dec_deg)
    radius = max(12.0, math.log10(distance_ly + 1.0) * 95.0) * scale
    x = radius * math.cos(dec) * math.cos(ra)
    y = radius * math.sin(dec)
    z = radius * math.cos(dec) * math.sin(ra)
    return [round(x, 3), round(y, 3), round(z, 3)]


def build_core_catalog() -> list[dict]:
    stars = []
    for name, ra, dec, distance_ly, mag, spec in BRIGHT_STARS:
        stars.append(
            {
                "name": name,
                "ra": ra,
                "dec": dec,
                "distance_ly": distance_ly,
                "mag": mag,
                "spectral_type": spec,
                "color": spectral_color(spec),
                "position": radec_to_xyz(ra, dec, distance_ly),
            }
        )
    return stars


def build_lod_catalog(count: int = 1800, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    stars = []
    for index in range(count):
        arm = rng.randrange(4)
        radius = math.sqrt(rng.random()) * 1450.0 + 70.0
        angle = arm * (math.pi / 2.0) + radius * 0.0105 + rng.gauss(0.0, 0.30)
        thickness = max(8.0, radius * 0.022)
        x = math.cos(angle) * radius + rng.gauss(0.0, thickness)
        z = math.sin(angle) * radius + rng.gauss(0.0, thickness)
        y = rng.gauss(0.0, 18.0 + radius * 0.015)
        mag = round(rng.uniform(3.0, 10.5), 2)
        color_roll = rng.random()
        if color_roll < 0.10:
            color = "#aabfff"
        elif color_roll < 0.55:
            color = "#fff4d8"
        elif color_roll < 0.82:
            color = "#ffd2a1"
        else:
            color = "#ffb07c"
        stars.append(
            {
                "id": index,
                "position": [round(x, 2), round(y, 2), round(z, 2)],
                "mag": mag,
                "color": color,
            }
        )
    return stars


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    LOD_DIR.mkdir(exist_ok=True)

    core = build_core_catalog()
    lod = build_lod_catalog()

    (DATA_DIR / "stars-core.json").write_text(
        json.dumps(core, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    (LOD_DIR / "lod1.json").write_text(
        json.dumps(lod, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print(f"Wrote {len(core)} core stars to {DATA_DIR / 'stars-core.json'}")
    print(f"Wrote {len(lod)} LOD stars to {LOD_DIR / 'lod1.json'}")


if __name__ == "__main__":
    main()
