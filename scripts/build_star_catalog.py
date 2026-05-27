import json
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LOD_DIR = DATA_DIR / "stars-lod"


CORE_STARS = [
    {"name": "Sirius", "ra": 101.287, "dec": -16.716, "distance_ly": 8.60, "mag": -1.46, "spectral_type": "A1V", "category": "bright_anchor"},
    {"name": "Canopus", "ra": 95.988, "dec": -52.696, "distance_ly": 310.0, "mag": -0.74, "spectral_type": "A9II", "category": "bright_anchor"},
    {"name": "Alpha Centauri A/B", "ra": 219.902, "dec": -60.834, "distance_ly": 4.37, "mag": -0.27, "spectral_type": "G2V/K1V", "category": "notable_nearby_system", "note": "Nearest stellar system; Alpha Centauri A and B are Sun-like binary components."},
    {"name": "Proxima Centauri", "ra": 217.429, "dec": -62.679, "distance_ly": 4.25, "mag": 11.13, "spectral_type": "M5.5Ve", "category": "habitability_interest", "note": "Hosts Proxima Cen b, the nearest confirmed exoplanet and a temperate terrestrial candidate."},
    {"name": "Barnard's Star", "ra": 269.454, "dec": 4.668, "distance_ly": 5.96, "mag": 9.54, "spectral_type": "M4V", "category": "notable_nearby_system", "note": "High proper-motion nearby red dwarf with confirmed planet candidates in the project dataset."},
    {"name": "Wolf 359", "ra": 164.120, "dec": 7.014, "distance_ly": 7.86, "mag": 13.54, "spectral_type": "M6V", "category": "nearby_red_dwarf"},
    {"name": "Lalande 21185", "ra": 165.830, "dec": 35.970, "distance_ly": 8.31, "mag": 7.49, "spectral_type": "M2V", "category": "nearby_red_dwarf"},
    {"name": "Ross 128", "ra": 176.937, "dec": 0.804, "distance_ly": 11.01, "mag": 11.13, "spectral_type": "M4V", "category": "habitability_interest", "note": "Hosts nearby temperate terrestrial-mass candidate Ross 128 b."},
    {"name": "Tau Ceti", "ra": 26.017, "dec": -15.938, "distance_ly": 11.91, "mag": 3.50, "spectral_type": "G8.5V", "category": "sun_like_interest", "note": "Nearby Sun-like star often used as a SETI and planetary-system reference target."},
    {"name": "Epsilon Eridani", "ra": 53.233, "dec": -9.458, "distance_ly": 10.47, "mag": 3.73, "spectral_type": "K2V", "category": "nearby_planet_host"},
    {"name": "YZ Ceti", "ra": 18.127, "dec": -16.998, "distance_ly": 12.11, "mag": 12.02, "spectral_type": "M4.5V", "category": "nearby_planet_host"},
    {"name": "Teegarden's Star", "ra": 43.253, "dec": 16.881, "distance_ly": 12.50, "mag": 15.08, "spectral_type": "M7V", "category": "habitability_interest", "note": "Hosts nearby temperate Earth-mass candidates Teegarden's Star b and c."},
    {"name": "Wolf 1069", "ra": 307.575, "dec": 58.575, "distance_ly": 31.2, "mag": 13.50, "spectral_type": "M5V", "category": "habitability_interest", "note": "Hosts terrestrial-mass habitable-zone candidate Wolf 1069 b."},
    {"name": "GJ 1002", "ra": 0.736, "dec": -7.538, "distance_ly": 15.81, "mag": 13.76, "spectral_type": "M5.5V", "category": "habitability_interest", "note": "Hosts nearby temperate low-mass candidates GJ 1002 b and c."},
    {"name": "GJ 667 C", "ra": 259.745, "dec": -34.996, "distance_ly": 23.63, "mag": 10.22, "spectral_type": "M1.5V", "category": "habitability_interest", "note": "Nearby multi-planet red-dwarf system with historically important habitable-zone candidates."},
    {"name": "TRAPPIST-1", "ra": 346.623, "dec": -5.041, "distance_ly": 40.54, "mag": 18.80, "spectral_type": "M8V", "category": "habitability_interest", "note": "Compact system with multiple temperate terrestrial-size planets."},
    {"name": "Gliese 12", "ra": 12.549, "dec": 13.345, "distance_ly": 39.82, "mag": 12.60, "spectral_type": "M3V", "category": "habitability_interest", "note": "Hosts nearby transiting terrestrial-size temperate planet Gliese 12 b."},
    {"name": "LHS 1140", "ra": 4.493, "dec": -15.272, "distance_ly": 48.8, "mag": 14.15, "spectral_type": "M4.5V", "category": "habitability_interest", "note": "Hosts LHS 1140 b, a major habitable-zone atmosphere follow-up target."},
    {"name": "TOI-700", "ra": 93.358, "dec": -65.579, "distance_ly": 101.4, "mag": 13.15, "spectral_type": "M2V", "category": "habitability_interest", "note": "Hosts TESS Earth-size habitable-zone candidates TOI-700 d and e."},
    {"name": "K2-18", "ra": 172.560, "dec": 7.588, "distance_ly": 124.0, "mag": 13.50, "spectral_type": "M2.5V", "category": "biosignature_interest", "note": "Hosts temperate sub-Neptune K2-18 b, an atmospheric biosignature-interest target."},
    {"name": "Kepler-186", "ra": 298.653, "dec": 43.956, "distance_ly": 579.0, "mag": 14.62, "spectral_type": "M1V", "category": "habitability_interest", "note": "Hosts classic Earth-size habitable-zone candidate Kepler-186 f."},
    {"name": "Kepler-442", "ra": 285.366, "dec": 39.281, "distance_ly": 1190.0, "mag": 14.98, "spectral_type": "K5V", "category": "habitability_interest", "note": "Hosts Kepler-442 b, a frequently cited super-Earth habitable-zone candidate."},
    {"name": "Kepler-452", "ra": 296.004, "dec": 44.277, "distance_ly": 1799.0, "mag": 13.43, "spectral_type": "G2V", "category": "habitability_interest", "note": "Sun-like host of well-known habitable-zone candidate Kepler-452 b."},
    {"name": "Arcturus", "ra": 213.915, "dec": 19.182, "distance_ly": 36.7, "mag": -0.05, "spectral_type": "K1.5III", "category": "bright_anchor"},
    {"name": "Vega", "ra": 279.234, "dec": 38.784, "distance_ly": 25.0, "mag": 0.03, "spectral_type": "A0V", "category": "bright_anchor"},
    {"name": "Capella", "ra": 79.172, "dec": 45.998, "distance_ly": 42.9, "mag": 0.08, "spectral_type": "G8III", "category": "bright_anchor"},
    {"name": "Rigel", "ra": 78.634, "dec": -8.202, "distance_ly": 860.0, "mag": 0.13, "spectral_type": "B8Ia", "category": "bright_anchor"},
    {"name": "Procyon", "ra": 114.825, "dec": 5.225, "distance_ly": 11.46, "mag": 0.34, "spectral_type": "F5IV", "category": "bright_anchor"},
    {"name": "Betelgeuse", "ra": 88.793, "dec": 7.407, "distance_ly": 548.0, "mag": 0.42, "spectral_type": "M1Iab", "category": "bright_anchor"},
    {"name": "Altair", "ra": 297.696, "dec": 8.868, "distance_ly": 16.7, "mag": 0.77, "spectral_type": "A7V", "category": "bright_anchor"},
    {"name": "Fomalhaut", "ra": 344.413, "dec": -29.622, "distance_ly": 25.1, "mag": 1.16, "spectral_type": "A3V", "category": "bright_anchor"},
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
    for star in CORE_STARS:
        stars.append(
            {
                **star,
                "color": spectral_color(star["spectral_type"]),
                "position": radec_to_xyz(star["ra"], star["dec"], star["distance_ly"]),
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
