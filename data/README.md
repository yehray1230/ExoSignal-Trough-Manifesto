# Star And Exoplanet Catalog Data

This directory contains the compact star layers used by the 3D scene.
The exoplanet target catalog is written to the project root as `data.js`
because the static HTML app loads it directly.

## Files

| File | Purpose | Source |
|---|---|---|
| `stars-core.json` | Compact real-star anchor layer with bright stars, nearby systems, and habitability-interest host stars. | Curated from common astronomical catalog values in `scripts/build_star_catalog.py`. |
| `stars-lod/lod1.json` | Procedural background starfield for depth and visual density. | Reproducible deterministic generator in `scripts/build_star_catalog.py`. |
| `bl-observations.json` | Lightweight Breakthrough Listen observation metadata grouped by target, telescope, MJD, frequency, and file type. | `scripts/fetch_breakthrough_listen.py` using the public Open Data Archive API. |
| `../data.js` | Exoplanet target catalog consumed by the app. | NASA Exoplanet Archive TAP `pscomppars` table plus local interpretive annotations. |

## Exoplanet Fields

`fetch_exoplanets.py` now preserves the original distance fields used by the app and adds richer planet, host-star, and sky-position metadata:

| Field | Meaning |
|---|---|
| `pl_name`, `hostname` | Planet and host-star names. |
| `sy_dist`, `distance_ly` | System distance in parsecs and light-years. |
| `ra`, `dec` | Host-star sky position in degrees, used by the 3D visualization when available. |
| `pl_orbper`, `pl_orbsmax` | Orbital period and semi-major axis. |
| `pl_rade`, `pl_bmasse`, `pl_eqt` | Planet radius, mass, and equilibrium temperature when available. |
| `st_spectype`, `st_teff`, `st_rad`, `st_mass` | Host-star spectral type and basic stellar parameters. |
| `disc_year`, `discoverymethod` | Discovery year and method. |
| `signal_year`, `required_power_w` | Project-derived light-travel and radio-power model fields. |
| `bl_observed`, `bl_observation_count`, `bl_first_observed_year`, `bl_latest_observed_year`, `bl_signal_year` | Breakthrough Listen metadata fields. `bl_signal_year` uses the latest matched BL observation year minus light-travel distance, while `signal_year` keeps the project-wide 2026 baseline. |
| `bl_telescopes`, `bl_file_types`, `bl_observations` | Compact observation provenance for matched targets. These are observation-window metadata, not detections of artificial signals. |
| `isHabitable`, `target_priority`, `interest_tags`, `habitability_note` | Local annotations for well-known habitability or biosignature-interest targets. These are labels for prioritization and visualization, not claims of confirmed life. |

## Regeneration

Refresh exoplanet data from NASA:

```bash
python fetch_exoplanets.py
```

Refresh Breakthrough Listen observation metadata, then regenerate exoplanet data so the matched fields are embedded in `data.js`:

```bash
python scripts/fetch_breakthrough_listen.py
python fetch_exoplanets.py
```

Regenerate the compact star layers:

```bash
python scripts/build_star_catalog.py
```

## Interpretation Limits

The project marks targets such as Proxima Cen b, TRAPPIST-1 e/f/g, LHS 1140 b, Kepler-186 f, Kepler-442 b, Kepler-452 b, K2-18 b, and similar objects as habitability-interest targets because they are widely discussed as temperate, habitable-zone, terrestrial-size, or atmospheric follow-up candidates. This is a visualization and selection-bias aid, not a biological detection claim.
