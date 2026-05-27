import csv
import io
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path


TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
OBSERVED_YEAR = 2026
PARSEC_TO_LIGHT_YEAR = 3.26156
FAST_BASELINE_W_PER_LY2 = 1.12e11
ROOT = Path(__file__).resolve().parent
BL_OBSERVATIONS_PATH = ROOT / "data" / "bl-observations.json"


TARGET_ANNOTATIONS = {
    "Proxima Cen b": {
        "isHabitable": True,
        "target_priority": 1,
        "interest_tags": ["nearest exoplanet", "habitable-zone candidate", "red-dwarf host"],
        "habitability_note": "Nearest confirmed exoplanet and a commonly discussed temperate terrestrial candidate around Proxima Centauri.",
    },
    "TRAPPIST-1 d": {
        "isHabitable": True,
        "target_priority": 1,
        "interest_tags": ["TRAPPIST-1 system", "temperate terrestrial candidate"],
        "habitability_note": "One of the compact TRAPPIST-1 terrestrial planets often considered in comparative habitability studies.",
    },
    "TRAPPIST-1 e": {
        "isHabitable": True,
        "target_priority": 1,
        "interest_tags": ["TRAPPIST-1 system", "habitable-zone candidate", "terrestrial-size"],
        "habitability_note": "Frequently highlighted as one of the strongest temperate terrestrial candidates in the TRAPPIST-1 system.",
    },
    "TRAPPIST-1 f": {
        "isHabitable": True,
        "target_priority": 1,
        "interest_tags": ["TRAPPIST-1 system", "habitable-zone candidate", "terrestrial-size"],
        "habitability_note": "Outer temperate TRAPPIST-1 planet with strong astrobiology interest.",
    },
    "TRAPPIST-1 g": {
        "isHabitable": True,
        "target_priority": 1,
        "interest_tags": ["TRAPPIST-1 system", "habitable-zone candidate", "terrestrial-size"],
        "habitability_note": "Outer TRAPPIST-1 habitable-zone candidate used in many atmospheric follow-up studies.",
    },
    "LHS 1140 b": {
        "isHabitable": True,
        "target_priority": 1,
        "interest_tags": ["habitable-zone candidate", "super-Earth", "atmosphere follow-up"],
        "habitability_note": "Nearby transiting super-Earth in the habitable zone and a major atmosphere-characterization target.",
    },
    "Teegarden's Star b": {
        "isHabitable": True,
        "target_priority": 1,
        "interest_tags": ["habitable-zone candidate", "nearby red-dwarf host"],
        "habitability_note": "Nearby temperate Earth-mass candidate around Teegarden's Star.",
    },
    "Teegarden's Star c": {
        "isHabitable": True,
        "target_priority": 2,
        "interest_tags": ["habitable-zone candidate", "nearby red-dwarf host"],
        "habitability_note": "Nearby temperate candidate often grouped with Teegarden's Star b for habitability studies.",
    },
    "GJ 1002 b": {
        "isHabitable": True,
        "target_priority": 1,
        "interest_tags": ["habitable-zone candidate", "nearby red-dwarf host"],
        "habitability_note": "Nearby low-mass temperate planet candidate around the quiet M dwarf GJ 1002.",
    },
    "GJ 1002 c": {
        "isHabitable": True,
        "target_priority": 1,
        "interest_tags": ["habitable-zone candidate", "nearby red-dwarf host"],
        "habitability_note": "Nearby low-mass temperate planet candidate around the quiet M dwarf GJ 1002.",
    },
    "Ross 128 b": {
        "isHabitable": True,
        "target_priority": 2,
        "interest_tags": ["nearby terrestrial candidate", "temperate candidate"],
        "habitability_note": "Nearby temperate terrestrial-mass candidate around a relatively quiet red dwarf.",
    },
    "Wolf 1069 b": {
        "isHabitable": True,
        "target_priority": 2,
        "interest_tags": ["habitable-zone candidate", "terrestrial-mass"],
        "habitability_note": "Terrestrial-mass habitable-zone candidate around the nearby M dwarf Wolf 1069.",
    },
    "Gliese 12 b": {
        "isHabitable": True,
        "target_priority": 2,
        "interest_tags": ["temperate candidate", "transiting terrestrial-size"],
        "habitability_note": "Nearby transiting terrestrial-size planet with equilibrium temperature in a follow-up-friendly range.",
    },
    "TOI-700 d": {
        "isHabitable": True,
        "target_priority": 2,
        "interest_tags": ["habitable-zone candidate", "TESS discovery"],
        "habitability_note": "TESS-discovered Earth-size habitable-zone candidate in the TOI-700 system.",
    },
    "TOI-700 e": {
        "isHabitable": True,
        "target_priority": 2,
        "interest_tags": ["habitable-zone candidate", "TESS discovery"],
        "habitability_note": "Additional Earth-size habitable-zone candidate in the TOI-700 system.",
    },
    "Kepler-186 f": {
        "isHabitable": True,
        "target_priority": 2,
        "interest_tags": ["classic habitable-zone candidate", "Earth-size"],
        "habitability_note": "Classic Earth-size habitable-zone candidate discovered by Kepler.",
    },
    "Kepler-442 b": {
        "isHabitable": True,
        "target_priority": 2,
        "interest_tags": ["habitable-zone candidate", "super-Earth"],
        "habitability_note": "Often ranked as a strong Kepler habitable-zone candidate, though much farther away than nearby M-dwarf targets.",
    },
    "Kepler-452 b": {
        "isHabitable": True,
        "target_priority": 3,
        "interest_tags": ["habitable-zone candidate", "solar-type host"],
        "habitability_note": "Well-known Kepler candidate orbiting a Sun-like star, but distant and larger than Earth.",
    },
    "K2-18 b": {
        "isHabitable": True,
        "target_priority": 2,
        "interest_tags": ["temperate sub-Neptune", "atmospheric biosignature interest"],
        "habitability_note": "Temperate sub-Neptune with strong atmospheric interest; habitability is debated because it is not an Earth twin.",
    },
    "GJ 667 C c": {
        "isHabitable": True,
        "target_priority": 3,
        "interest_tags": ["habitable-zone candidate", "nearby multi-planet system"],
        "habitability_note": "Historically important nearby habitable-zone candidate in the GJ 667 C system.",
    },
}


NASA_URLS = {
    "Proxima Cen b": "https://exoplanets.nasa.gov/exoplanet/proxima-centauri-b/",
    "Ross 128 b": "https://exoplanets.nasa.gov/exoplanet/ross-128-b/",
    "TRAPPIST-1 d": "https://exoplanets.nasa.gov/star-system/trappist-1/",
    "TRAPPIST-1 e": "https://exoplanets.nasa.gov/star-system/trappist-1/",
    "TRAPPIST-1 f": "https://exoplanets.nasa.gov/star-system/trappist-1/",
    "TRAPPIST-1 g": "https://exoplanets.nasa.gov/star-system/trappist-1/",
    "LHS 1140 b": "https://exoplanets.nasa.gov/exoplanet/lhs-1140-b/",
    "Kepler-186 f": "https://exoplanets.nasa.gov/exoplanet/kepler-186-f/",
    "Kepler-452 b": "https://exoplanets.nasa.gov/exoplanet/kepler-452-b/",
    "K2-18 b": "https://exoplanets.nasa.gov/exoplanet/k2-18-b/",
}


QUERY = """
SELECT
    pl_name,
    hostname,
    sy_dist,
    ra,
    dec,
    pl_orbper,
    pl_orbsmax,
    pl_rade,
    pl_bmasse,
    pl_eqt,
    st_spectype,
    st_teff,
    st_rad,
    st_mass,
    disc_year,
    discoverymethod
FROM pscomppars
WHERE sy_dist IS NOT NULL
ORDER BY sy_dist ASC
"""


NUMERIC_FIELDS = {
    "sy_dist",
    "ra",
    "dec",
    "pl_orbper",
    "pl_orbsmax",
    "pl_rade",
    "pl_bmasse",
    "pl_eqt",
    "st_teff",
    "st_rad",
    "st_mass",
    "disc_year",
}


def parse_float(value):
    if value is None or value == "":
        return None
    try:
        numeric = float(value)
    except ValueError:
        return None
    if math.isnan(numeric):
        return None
    return numeric


def fetch_csv():
    params = urllib.parse.urlencode({"query": QUERY, "format": "csv"}).encode("utf-8")
    request = urllib.request.Request(TAP_URL, data=params, method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def normalize_name(value):
    return "".join(char for char in str(value or "").lower() if char.isalnum())


def angular_distance_deg(ra1, dec1, ra2, dec2):
    if None in (ra1, dec1, ra2, dec2):
        return None
    ra1_rad = math.radians(ra1)
    dec1_rad = math.radians(dec1)
    ra2_rad = math.radians(ra2)
    dec2_rad = math.radians(dec2)
    cos_angle = (
        math.sin(dec1_rad) * math.sin(dec2_rad)
        + math.cos(dec1_rad) * math.cos(dec2_rad) * math.cos(ra1_rad - ra2_rad)
    )
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_angle))))


def load_breakthrough_observations():
    if not BL_OBSERVATIONS_PATH.exists():
        return []
    payload = json.loads(BL_OBSERVATIONS_PATH.read_text(encoding="utf-8"))
    return payload.get("observations", [])


def match_breakthrough_observations(row, observations):
    host_key = normalize_name(row.get("hostname"))
    matches = []
    for observation in observations:
        source_key = normalize_name(observation.get("source_host"))
        name_match = bool(host_key and source_key and host_key == source_key)
        separation = angular_distance_deg(
            row.get("ra"),
            row.get("dec"),
            observation.get("ra"),
            observation.get("dec"),
        )
        coordinate_match = separation is not None and separation <= 0.2
        if name_match or coordinate_match:
            compact = {
                "target_name": observation.get("target_name"),
                "telescope": observation.get("telescope"),
                "utc": observation.get("utc"),
                "mjd": observation.get("mjd"),
                "observation_year": observation.get("observation_year"),
                "center_freq_mhz": observation.get("center_freq_mhz"),
                "file_type": observation.get("file_type"),
                "quality": observation.get("quality"),
                "file_count": observation.get("file_count"),
                "sample_file_url": observation.get("sample_file_url"),
            }
            matches.append(compact)

    def sort_key(item):
        year = item.get("observation_year")
        return year if isinstance(year, (int, float)) else math.inf

    return sorted(matches, key=sort_key)


def enrich_with_breakthrough(row, observations):
    matches = match_breakthrough_observations(row, observations)
    years = [item["observation_year"] for item in matches if isinstance(item.get("observation_year"), (int, float))]
    row["bl_observed"] = bool(matches)
    row["bl_observation_count"] = sum(item.get("file_count") or 1 for item in matches)
    row["bl_observation_group_count"] = len(matches)
    row["bl_first_observed_year"] = min(years) if years else None
    row["bl_latest_observed_year"] = max(years) if years else None
    row["bl_signal_year"] = (row["bl_latest_observed_year"] - row["distance_ly"]) if years else None
    row["bl_telescopes"] = sorted({item["telescope"] for item in matches if item.get("telescope")})
    row["bl_file_types"] = sorted({item["file_type"] for item in matches if item.get("file_type")})
    row["bl_observations"] = matches[:6]
    return row


def enrich_row(row):
    enriched = {}
    for key, value in row.items():
        enriched[key] = parse_float(value) if key in NUMERIC_FIELDS else (value or None)

    distance_ly = enriched["sy_dist"] * PARSEC_TO_LIGHT_YEAR
    enriched["distance_ly"] = distance_ly
    enriched["signal_year"] = OBSERVED_YEAR - distance_ly
    enriched["required_power_w"] = FAST_BASELINE_W_PER_LY2 * (distance_ly**2)

    annotation = TARGET_ANNOTATIONS.get(enriched["pl_name"], {})
    enriched["isHabitable"] = bool(annotation.get("isHabitable", False))
    enriched["target_priority"] = annotation.get("target_priority", 9)
    enriched["interest_tags"] = annotation.get("interest_tags", [])
    enriched["habitability_note"] = annotation.get("habitability_note")
    enriched["nasaUrl"] = NASA_URLS.get(enriched["pl_name"])
    return enriched


def fetch_exoplanet_data():
    raw_csv = fetch_csv()
    reader = csv.DictReader(io.StringIO(raw_csv))
    breakthrough_observations = load_breakthrough_observations()
    rows = [enrich_with_breakthrough(enrich_row(row), breakthrough_observations) for row in reader]
    rows.sort(key=lambda item: (item["target_priority"], item["distance_ly"]))
    return rows


def main():
    try:
        rows = fetch_exoplanet_data()
    except Exception as exc:
        print(f"NASA Exoplanet Archive request failed: {exc}", file=sys.stderr)
        raise

    js_content = "window.EXOPLANETS_DATA = " + json.dumps(
        rows, ensure_ascii=False, separators=(",", ":")
    ) + ";"
    with open("data.js", "w", encoding="utf-8") as output:
        output.write(js_content)

    highlighted = sum(1 for row in rows if row["isHabitable"])
    observed = sum(1 for row in rows if row["bl_observed"])
    print(f"Wrote {len(rows)} exoplanets to data.js")
    print(f"Highlighted {highlighted} habitability-interest targets")
    print(f"Matched {observed} targets with Breakthrough Listen observation metadata")


if __name__ == "__main__":
    main()
