#!/usr/bin/env python3
"""Drake-equation and radio-window scenario simulator.

This module is intentionally self-contained and uses only Python's standard
library. It reads the project's existing data.js catalog, turns Drake equation
terms into a per-target communication probability weight, applies a configurable
radio communication time window, and writes CSV + a standalone HTML report.
"""

from __future__ import annotations

import csv
import json
import math
import random
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "outputs"


@dataclass(frozen=True)
class Target:
    name: str
    host: str
    distance_ly: float
    required_power_w: float
    bl_observed: bool = False
    bl_observation_years: tuple[float, ...] = ()
    bl_latest_observed_year: float | None = None
    bl_observation_count: int = 0
    bl_telescopes: tuple[str, ...] = ()


def load_config() -> dict:
    return json.loads((HERE / "config.json").read_text(encoding="utf-8"))


def load_targets(limit: int | None = None) -> list[Target]:
    text = (ROOT / "data.js").read_text(encoding="utf-8")
    match = re.search(r"window\.EXOPLANETS_DATA\s*=\s*(\[.*\]);?\s*$", text, re.S)
    if not match:
        raise ValueError("Could not find window.EXOPLANETS_DATA in data.js")
    rows = json.loads(match.group(1))
    targets = [
        Target(
            name=row.get("pl_name", "unknown"),
            host=row.get("hostname", "unknown"),
            distance_ly=float(row["distance_ly"]),
            required_power_w=float(row["required_power_w"]),
            bl_observed=bool(row.get("bl_observed")),
            bl_observation_years=tuple(
                float(item["observation_year"])
                for item in row.get("bl_observations", [])
                if isinstance(item.get("observation_year"), (int, float))
            ),
            bl_latest_observed_year=(
                float(row["bl_latest_observed_year"])
                if isinstance(row.get("bl_latest_observed_year"), (int, float))
                else None
            ),
            bl_observation_count=int(row.get("bl_observation_count") or 0),
            bl_telescopes=tuple(row.get("bl_telescopes") or ()),
        )
        for row in rows
        if row.get("distance_ly") is not None and row.get("required_power_w") is not None
    ]
    targets.sort(key=lambda t: t.distance_ly)
    return targets[:limit] if limit else targets


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normal_pdf(x: float, mu: float, sigma: float) -> float:
    if sigma <= 0:
        return 1.0 if abs(x - mu) < 0.5 else 0.0
    z = (x - mu) / sigma
    return math.exp(-0.5 * z * z) / (sigma * math.sqrt(2 * math.pi))


def normal_cdf(x: float, mu: float, sigma: float) -> float:
    if sigma <= 0:
        return 1.0 if x >= mu else 0.0
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0))))


def lognormal_pdf(x: float, mean: float, std: float) -> float:
    if x <= 0 or mean <= 0 or std <= 0:
        return 0.0
    sigma2 = math.log(1.0 + (std * std) / (mean * mean))
    sigma = math.sqrt(max(sigma2, 1e-8))
    mu = math.log(mean) - sigma2 / 2.0
    z = (math.log(x) - mu) / sigma
    return math.exp(-0.5 * z * z) / (x * sigma * math.sqrt(2.0 * math.pi))


def gamma_pdf(x: float, mean_value: float, std: float) -> float:
    if x <= 0 or mean_value <= 0 or std <= 0:
        return 0.0
    shape = max((mean_value / std) ** 2, 1e-4)
    scale = max((std * std) / mean_value, 1e-4)
    return math.exp(
        (shape - 1.0) * math.log(x)
        - x / scale
        - math.lgamma(shape)
        - shape * math.log(scale)
    )


def weighted_samples(kind: str, mean_value: float, std: float, count: int = 15) -> list[tuple[float, float]]:
    if kind == "fixed":
        return [(mean_value, 1.0)]
    safe_mean = max(mean_value, 1.0)
    safe_std = max(std, 1.0)
    max_value = max(safe_mean + 5.0 * safe_std, safe_mean * 4.0, 1.0)
    step = max_value / count
    samples: list[tuple[float, float]] = []
    total = 0.0
    for i in range(count):
        value = (i + 0.5) * step
        if kind == "normal":
            density = normal_pdf(value, safe_mean, safe_std)
        elif kind == "lognormal":
            density = lognormal_pdf(value, safe_mean, safe_std)
        elif kind == "gamma":
            density = gamma_pdf(value, safe_mean, safe_std)
        else:
            density = 0.0
        weight = max(0.0, density * step)
        samples.append((value, weight))
        total += weight
    if total <= 0:
        return [(safe_mean, 1.0)]
    return [(value, weight / total) for value, weight in samples]


def drake_weight(config: dict, radio_window_years: float, target_count: int) -> float:
    drake = config["drake"]
    non_lifetime_terms = (
        drake["fraction_with_planets"]
        * drake["habitable_planets_per_system"]
        * drake["fraction_life"]
        * drake["fraction_intelligence"]
        * drake["fraction_communicative"]
    )
    expected_galactic_civs = drake["star_formation_rate_per_year"] * non_lifetime_terms * radio_window_years
    # The catalog is a search sample, not the whole galaxy. Use the Drake value as
    # a sparse prior spread across catalog targets so probabilities remain bounded.
    return clamp(expected_galactic_civs / max(target_count, 1), 0.0, 0.95)


def detectability_weight(required_power_w: float, config: dict) -> float:
    max_power = config["communication"]["max_effective_transmit_power_w"] * correlation_power_factor(config)
    rolloff = max(config["communication"]["power_rolloff_decades"], 0.05)
    if required_power_w <= 0:
        return 0.0
    log_ratio = math.log10(required_power_w / max_power)
    # Logistic falloff in log-power space: near 1 below the assumed capability,
    # near 0 when required power is many decades too high.
    return 1.0 / (1.0 + math.exp(log_ratio / rolloff))


def correlation_power_factor(config: dict) -> float:
    civ = config["civilization"]
    communication = config["communication"]
    rigor = config.get("rigor", {})
    strength = float(rigor.get("assumption_correlation", 0.0))
    window_pressure = max(0.0, math.log10(max(float(civ["radio_window_years"]), 1.0) / 650.0))
    power_pressure = max(0.0, math.log10(float(communication["max_effective_transmit_power_w"]) / 1.0e18) / 4.0)
    penalty = strength * (0.35 * window_pressure + 0.2 * power_pressure)
    return clamp(1.0 - penalty, 0.35, 1.1)


def catalog_selection_weight(target: Target, config: dict) -> float:
    bias = float(config.get("rigor", {}).get("catalog_selection_bias", 0.0))
    distance_completeness = 1.0 / (1.0 + (max(target.distance_ly, 0.0) / 180.0) ** 2)
    data_completeness = 1.0 if target.required_power_w > 0 and target.distance_ly > 0 else 0.35
    bias_weight = clamp(0.2 + 0.8 * distance_completeness * data_completeness, 0.05, 1.0)
    return (1.0 - bias) + bias * bias_weight


def observability_weight(target: Target, config: dict) -> float:
    communication = config["communication"]
    return (
        detectability_weight(target.required_power_w, config)
        * catalog_selection_weight(target, config)
        * float(communication.get("beam_coverage", 1.0))
        * float(communication.get("duty_cycle", 1.0))
        * float(communication.get("frequency_coverage", 1.0))
    )


def observation_epoch_model(config: dict) -> str:
    return str(config.get("observation_epoch_model", "continuous"))


def target_observation_years(target: Target) -> tuple[float, ...]:
    if target.bl_observation_years:
        return target.bl_observation_years
    if target.bl_latest_observed_year is not None:
        return (target.bl_latest_observed_year,)
    return ()


def observation_epoch_weight(receive_year: float, target: Target, config: dict) -> float:
    if observation_epoch_model(config) != "breakthrough_listen":
        return 1.0
    years = target_observation_years(target)
    if not years:
        return 0.0
    sigma = max(float(config.get("bl_observation_window_years", 1.0)), 0.05)
    return max(math.exp(-0.5 * ((receive_year - year) / sigma) ** 2) for year in years)


def build_timing_context(config: dict) -> dict:
    civ = config["civilization"]
    timing_model = civ.get("timing_model", "normal")
    window_model = civ.get("radio_window_model", "fixed")
    window = max(float(civ["radio_window_years"]), float(civ["min_radio_window_years"]))
    window_std = max(float(civ.get("radio_window_std", window * 1.1)), 25.0)
    return {
        "timing_model": timing_model,
        "window_model": window_model,
        "development_samples": []
        if timing_model == "normal"
        else weighted_samples(
            timing_model,
            float(civ["development_duration_mean"]),
            float(civ["development_duration_std"]),
            15,
        ),
        "window_samples": []
        if window_model == "infinite"
        else [(window, 1.0)]
        if window_model == "fixed"
        else weighted_samples("lognormal", window, window_std, 11),
    }


def build_continuous_timing_context(config: dict) -> dict:
    context = build_timing_context(config)
    context["window_model"] = "infinite"
    context["window_samples"] = []
    return context


def build_synchronization_hypothesis_context(config: dict) -> dict:
    context = build_timing_context(config)
    if context["window_model"] == "infinite":
        context["window_model"] = "fixed"
        civ = config["civilization"]
        window = max(float(civ["radio_window_years"]), float(civ["min_radio_window_years"]))
        context["window_samples"] = [(window, 1.0)]
    return context


def active_probability_at(emit_year: float, config: dict, context: dict) -> float:
    civ = config["civilization"]
    timing_model = context["timing_model"]
    window_model = context["window_model"]
    window = max(float(civ["radio_window_years"]), float(civ["min_radio_window_years"]))
    if window_model == "infinite":
        if timing_model == "normal":
            start_mu = float(civ["birth_year_mean"]) + float(civ["development_duration_mean"])
            start_sigma = math.sqrt(float(civ["birth_year_std"]) ** 2 + float(civ["development_duration_std"]) ** 2)
            return normal_cdf(emit_year, start_mu, start_sigma)

        development_samples = context["development_samples"] or [(float(civ["development_duration_mean"]), 1.0)]
        probability = 0.0
        for development_duration, dev_weight in development_samples:
            probability += dev_weight * normal_cdf(
                emit_year - development_duration,
                float(civ["birth_year_mean"]),
                float(civ["birth_year_std"]),
            )
        return clamp(probability, 0.0, 1.0)

    if timing_model == "normal" and window_model == "fixed":
        start_mu = float(civ["birth_year_mean"]) + float(civ["development_duration_mean"])
        start_sigma = math.sqrt(float(civ["birth_year_std"]) ** 2 + float(civ["development_duration_std"]) ** 2)
        return normal_cdf(emit_year, start_mu, start_sigma) - normal_cdf(emit_year - window, start_mu, start_sigma)

    development_samples = context["development_samples"] or [(float(civ["development_duration_mean"]), 1.0)]
    probability = 0.0
    for development_duration, dev_weight in development_samples:
        for window_duration, window_weight in context["window_samples"]:
            start_before_receive = normal_cdf(
                emit_year - development_duration,
                float(civ["birth_year_mean"]),
                float(civ["birth_year_std"]),
            )
            start_before_window = normal_cdf(
                emit_year - development_duration - window_duration,
                float(civ["birth_year_mean"]),
                float(civ["birth_year_std"]),
            )
            probability += dev_weight * window_weight * max(0.0, start_before_receive - start_before_window)
    return clamp(probability, 0.0, 1.0)


def arrival_density_at(receive_year: float, target: Target, config: dict, context: dict) -> float:
    civ = config["civilization"]
    emit_year = receive_year - target.distance_ly
    if context["timing_model"] == "normal":
        mu = float(civ["birth_year_mean"]) + float(civ["development_duration_mean"])
        sigma = math.sqrt(float(civ["birth_year_std"]) ** 2 + float(civ["development_duration_std"]) ** 2)
        return normal_pdf(emit_year, mu, sigma)

    density = 0.0
    for development_duration, dev_weight in context["development_samples"]:
        density += dev_weight * normal_pdf(
            emit_year - development_duration,
            float(civ["birth_year_mean"]),
            float(civ["birth_year_std"]),
        )
    return density


def arrival_probability_series(targets: list[Target], config: dict) -> list[dict]:
    civ = config["civilization"]
    start = int(config["observation_year_start"])
    end = int(config["observation_year_end"])
    step = max(int(config["year_step"]), 1)
    window = max(float(civ["radio_window_years"]), float(civ["min_radio_window_years"]))
    continuous_context = build_continuous_timing_context(config)
    synchronization_context = build_synchronization_hypothesis_context(config)
    base_weight = drake_weight(config, window, len(targets))

    rows = []
    for year in range(start, end + 1, step):
        no_detection = 1.0
        no_detection_synchronized = 1.0
        expected_sources = 0.0
        expected_synchronized_sources = 0.0
        for target in targets:
            emit_year = year - target.distance_ly
            continuous_active_probability = active_probability_at(emit_year, config, continuous_context)
            synchronized_active_probability = active_probability_at(emit_year, config, synchronization_context)
            observability = observability_weight(target, config) * observation_epoch_weight(year, target, config)
            p = (
                base_weight
                * continuous_active_probability
                * observability
            )
            p_synchronized = (
                base_weight
                * synchronized_active_probability
                * observability
            )
            p = clamp(p, 0.0, 0.95)
            p_synchronized = clamp(p_synchronized, 0.0, 0.95)
            no_detection *= 1.0 - p
            no_detection_synchronized *= 1.0 - p_synchronized
            expected_sources += p
            expected_synchronized_sources += p_synchronized
        probability = 1.0 - no_detection
        synchronized_probability = 1.0 - no_detection_synchronized
        synchronization_loss_fraction = (
            clamp((probability - synchronized_probability) / probability, 0.0, 1.0)
            if probability > 0
            else 0.0
        )
        rows.append(
            {
                "year": year,
                "probability_at_least_one_signal": probability,
                "expected_detectable_sources": expected_sources,
                "window_limited_probability": synchronized_probability,
                "window_limited_expected_sources": expected_synchronized_sources,
                "synchronization_loss_fraction": synchronization_loss_fraction,
            }
        )
    return rows


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def clone_config(config: dict) -> dict:
    return json.loads(json.dumps(config))


def logit(value: float) -> float:
    safe = clamp(value, 1e-6, 1.0 - 1e-6)
    return math.log(safe / (1.0 - safe))


def inv_logit(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def sample_fraction(rng: random.Random, value: float, sigma: float = 0.65, lo: float = 0.001, hi: float = 1.0) -> float:
    return clamp(inv_logit(rng.gauss(logit(value), sigma)), lo, hi)


def sample_log_space(rng: random.Random, value: float, sigma_decades: float, lo: float, hi: float) -> float:
    safe = clamp(value, lo, hi)
    sampled = 10 ** rng.gauss(math.log10(safe), sigma_decades)
    return clamp(sampled, lo, hi)


def sample_lognormal_factor(rng: random.Random, value: float, sigma: float, lo: float, hi: float) -> float:
    safe = clamp(value, lo, hi)
    sampled = safe * math.exp(rng.gauss(0.0, sigma))
    return clamp(sampled, lo, hi)


def sample_positive_normal(rng: random.Random, value: float, std: float, lo: float, hi: float) -> float:
    sampled = rng.gauss(value, std)
    return clamp(sampled, lo, hi)


def sample_monte_carlo_config(config: dict, rng: random.Random) -> dict:
    scenario = clone_config(config)
    drake = scenario["drake"]
    civ = scenario["civilization"]
    communication = scenario["communication"]
    rigor = scenario.setdefault("rigor", {})

    drake["fraction_life"] = sample_fraction(rng, float(drake["fraction_life"]), 0.8)
    drake["fraction_intelligence"] = sample_fraction(rng, float(drake["fraction_intelligence"]), 0.8)
    drake["fraction_communicative"] = sample_fraction(rng, float(drake["fraction_communicative"]), 0.75)

    civ["birth_year_mean"] = sample_positive_normal(
        rng,
        float(civ["birth_year_mean"]),
        max(float(civ["birth_year_std"]) * 0.25, 250.0),
        -10000.0,
        10000.0,
    )
    civ["birth_year_std"] = sample_lognormal_factor(rng, float(civ["birth_year_std"]), 0.25, 50.0, 8000.0)
    civ["development_duration_mean"] = sample_positive_normal(
        rng,
        float(civ["development_duration_mean"]),
        max(float(civ["development_duration_std"]) * 0.25, 150.0),
        50.0,
        15000.0,
    )
    civ["development_duration_std"] = sample_lognormal_factor(
        rng,
        float(civ["development_duration_std"]),
        0.25,
        25.0,
        6000.0,
    )
    civ["radio_window_years"] = sample_lognormal_factor(
        rng,
        float(civ["radio_window_years"]),
        0.55,
        float(civ.get("min_radio_window_years", 25.0)),
        5000.0,
    )
    civ["radio_window_std"] = sample_lognormal_factor(
        rng,
        float(civ.get("radio_window_std", float(civ["radio_window_years"]) * 1.1)),
        0.4,
        25.0,
        5000.0,
    )

    communication["max_effective_transmit_power_w"] = sample_log_space(
        rng,
        float(communication["max_effective_transmit_power_w"]),
        0.75,
        1.0e12,
        1.0e22,
    )
    communication["power_rolloff_decades"] = sample_lognormal_factor(
        rng,
        float(communication["power_rolloff_decades"]),
        0.25,
        0.2,
        3.0,
    )
    communication["beam_coverage"] = sample_fraction(rng, float(communication.get("beam_coverage", 1.0)), 0.55, 0.01, 1.0)
    communication["duty_cycle"] = sample_fraction(rng, float(communication.get("duty_cycle", 1.0)), 0.55, 0.01, 1.0)
    communication["frequency_coverage"] = sample_fraction(
        rng,
        float(communication.get("frequency_coverage", 1.0)),
        0.55,
        0.01,
        1.0,
    )
    rigor["catalog_selection_bias"] = sample_fraction(rng, float(rigor.get("catalog_selection_bias", 0.0)), 0.55, 0.0, 1.0)
    rigor["assumption_correlation"] = sample_fraction(rng, float(rigor.get("assumption_correlation", 0.0)), 0.55, 0.0, 1.0)
    return scenario


def uncertainty_scenarios(config: dict) -> list[dict]:
    spread = float(config.get("rigor", {}).get("uncertainty_spread", 0.0))
    if spread <= 0:
        return [config]
    factors = [math.exp((q - 0.5) * 2.7 * spread) for q in [0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95]]
    scenarios = []
    for index, factor in enumerate(factors):
        inverse = factors[len(factors) - 1 - index]
        scenario = clone_config(config)
        drake = scenario["drake"]
        civ = scenario["civilization"]
        drake["fraction_life"] = clamp(float(drake["fraction_life"]) * factor, 0.001, 1.0)
        drake["fraction_intelligence"] = clamp(float(drake["fraction_intelligence"]) * inverse, 0.001, 1.0)
        drake["fraction_communicative"] = clamp(float(drake["fraction_communicative"]) * factor, 0.001, 1.0)
        civ["radio_window_years"] = clamp(float(civ["radio_window_years"]) * inverse, 25.0, 5000.0)
        scenarios.append(scenario)
    return scenarios


def add_uncertainty_band(targets: list[Target], config: dict, rows: list[dict]) -> list[dict]:
    scenarios = uncertainty_scenarios(config)
    if len(scenarios) == 1:
        for row in rows:
            row["probability_p05"] = row["probability_at_least_one_signal"]
            row["probability_p95"] = row["probability_at_least_one_signal"]
        return rows
    scenario_rows = [arrival_probability_series(targets, scenario) for scenario in scenarios]
    for index, row in enumerate(rows):
        values = [series[index]["probability_at_least_one_signal"] for series in scenario_rows if index < len(series)]
        row["probability_p05"] = quantile(values, 0.05)
        row["probability_p95"] = quantile(values, 0.95)
    return rows


def peak_summary(rows: list[dict]) -> tuple[float, int]:
    peak = max(rows, key=lambda r: r["probability_at_least_one_signal"])
    return float(peak["probability_at_least_one_signal"]), int(peak["year"])


def perturb_config(config: dict, path: tuple[str, str], direction: int) -> dict:
    scenario = clone_config(config)
    section, key = path
    value = float(scenario[section][key])
    ranges = {
        ("drake", "fraction_life"): (0.001, 1.0, 0.12),
        ("drake", "fraction_intelligence"): (0.001, 1.0, 0.12),
        ("drake", "fraction_communicative"): (0.001, 1.0, 0.12),
        ("civilization", "radio_window_years"): (25.0, 5000.0, value * 0.35),
        ("rigor", "catalog_selection_bias"): (0.0, 1.0, 0.12),
        ("communication", "beam_coverage"): (0.01, 1.0, 0.12),
        ("communication", "duty_cycle"): (0.01, 1.0, 0.12),
        ("communication", "frequency_coverage"): (0.01, 1.0, 0.12),
        ("rigor", "assumption_correlation"): (0.0, 1.0, 0.12),
        ("communication", "max_effective_transmit_power_w"): (1.0e12, 1.0e22, value * 4.0),
        ("communication", "power_rolloff_decades"): (0.2, 3.0, 0.25),
    }
    lo, hi, delta = ranges[path]
    scenario[section][key] = clamp(value + direction * delta, lo, hi)
    return scenario


def sensitivity_ranking(targets: list[Target], config: dict, baseline_rows: list[dict]) -> list[dict]:
    baseline_probability, baseline_year = peak_summary(baseline_rows)
    assumptions = [
        (("drake", "fraction_life"), "Life fraction"),
        (("drake", "fraction_intelligence"), "Intelligence fraction"),
        (("drake", "fraction_communicative"), "Communicative fraction"),
        (("civilization", "radio_window_years"), "Radio-window lifetime"),
        (("rigor", "catalog_selection_bias"), "Catalog selection bias"),
        (("communication", "beam_coverage"), "Beam coverage"),
        (("communication", "duty_cycle"), "Duty cycle"),
        (("communication", "frequency_coverage"), "Frequency coverage"),
        (("rigor", "assumption_correlation"), "Variable correlation"),
        (("communication", "max_effective_transmit_power_w"), "Transmit power"),
        (("communication", "power_rolloff_decades"), "Power rolloff"),
    ]
    rows = []
    for path, label in assumptions:
        low_probability, low_year = peak_summary(arrival_probability_series(targets, perturb_config(config, path, -1)))
        high_probability, high_year = peak_summary(arrival_probability_series(targets, perturb_config(config, path, 1)))
        probability_impact = max(abs(low_probability - baseline_probability), abs(high_probability - baseline_probability))
        year_impact = max(abs(low_year - baseline_year), abs(high_year - baseline_year))
        rows.append(
            {
                "assumption": label,
                "peak_probability_impact": probability_impact,
                "peak_year_impact": year_impact,
                "score": probability_impact / max(baseline_probability, 1e-6) + year_impact / 1000.0,
            }
        )
    return sorted(rows, key=lambda r: r["score"], reverse=True)


MONTE_CARLO_PARAMETERS = [
    ("fraction_life", ("drake", "fraction_life"), "Life fraction"),
    ("fraction_intelligence", ("drake", "fraction_intelligence"), "Intelligence fraction"),
    ("fraction_communicative", ("drake", "fraction_communicative"), "Communicative fraction"),
    ("birth_year_mean", ("civilization", "birth_year_mean"), "Birth-year mean"),
    ("development_duration_mean", ("civilization", "development_duration_mean"), "Development duration"),
    ("radio_window_years", ("civilization", "radio_window_years"), "Radio-window lifetime"),
    ("max_effective_transmit_power_w", ("communication", "max_effective_transmit_power_w"), "Transmit power"),
    ("power_rolloff_decades", ("communication", "power_rolloff_decades"), "Power rolloff"),
    ("beam_coverage", ("communication", "beam_coverage"), "Beam coverage"),
    ("duty_cycle", ("communication", "duty_cycle"), "Duty cycle"),
    ("frequency_coverage", ("communication", "frequency_coverage"), "Frequency coverage"),
    ("catalog_selection_bias", ("rigor", "catalog_selection_bias"), "Catalog selection bias"),
    ("assumption_correlation", ("rigor", "assumption_correlation"), "Variable correlation"),
]


def config_value(config: dict, path: tuple[str, str]) -> float:
    section, key = path
    return float(config[section][key])


def probability_at_summary_year(rows: list[dict], year: int) -> float:
    nearest = min(rows, key=lambda r: abs(int(r["year"]) - year))
    return float(nearest["probability_at_least_one_signal"])


def area_under_probability_curve(rows: list[dict]) -> float:
    if len(rows) < 2:
        return float(rows[0]["probability_at_least_one_signal"]) if rows else 0.0
    area = 0.0
    for previous, current in zip(rows, rows[1:]):
        year_delta = float(current["year"]) - float(previous["year"])
        probability_sum = float(previous["probability_at_least_one_signal"]) + float(current["probability_at_least_one_signal"])
        area += year_delta * probability_sum / 2.0
    return area


def rank_values(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][1] == ordered[index][1]:
            end += 1
        rank = (index + end - 1) / 2.0 + 1.0
        for ordered_index in range(index, end):
            ranks[ordered[ordered_index][0]] = rank
        index = end
    return ranks


def pearson_correlation(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mean_x = mean(xs)
    mean_y = mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denominator_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denominator_x <= 0 or denominator_y <= 0:
        return 0.0
    return numerator / (denominator_x * denominator_y)


def spearman_correlation(xs: list[float], ys: list[float]) -> float:
    return pearson_correlation(rank_values(xs), rank_values(ys))


def monte_carlo_influence(sample_rows: list[dict]) -> list[dict]:
    peak_values = [float(row["peak_probability"]) for row in sample_rows]
    rows = []
    for key, _path, label in MONTE_CARLO_PARAMETERS:
        values = [float(row[key]) for row in sample_rows]
        ordered = sorted(zip(values, peak_values), key=lambda item: item[0])
        decile_count = max(1, len(ordered) // 10)
        low_mean = mean(value for _parameter, value in ordered[:decile_count])
        high_mean = mean(value for _parameter, value in ordered[-decile_count:])
        correlation = spearman_correlation(values, peak_values)
        rows.append(
            {
                "assumption": label,
                "rank_correlation": correlation,
                "decile_lift": high_mean - low_mean,
                "score": abs(correlation) + abs(high_mean - low_mean),
            }
        )
    return sorted(rows, key=lambda row: row["score"], reverse=True)


def representative_monte_carlo_rows(sample_rows: list[dict]) -> list[dict]:
    if not sample_rows:
        return []
    ordered = sorted(sample_rows, key=lambda row: float(row["peak_probability"]))

    def nearest_by_probability(label: str, q: float) -> dict:
        target = quantile([float(row["peak_probability"]) for row in ordered], q)
        row = min(ordered, key=lambda candidate: abs(float(candidate["peak_probability"]) - target))
        return {"case": label, **row}

    maximum = max(sample_rows, key=lambda row: float(row["peak_probability"]))
    earliest = min(sample_rows, key=lambda row: (int(row["peak_year"]), -float(row["peak_probability"])))
    return [
        nearest_by_probability("p10 conservative", 0.10),
        nearest_by_probability("p50 median", 0.50),
        nearest_by_probability("p90 optimistic", 0.90),
        {"case": "maximum peak", **maximum},
        {"case": "earliest peak", **earliest},
    ]


def monte_carlo_sample_row(index: int, scenario: dict, rows: list[dict], summary_years: list[int]) -> dict:
    peak = max(rows, key=lambda row: row["probability_at_least_one_signal"])
    sample = {
        "sample": index,
        "peak_probability": float(peak["probability_at_least_one_signal"]),
        "peak_year": int(peak["year"]),
        "expected_sources_at_peak": float(peak["expected_detectable_sources"]),
        "area_under_probability_curve": area_under_probability_curve(rows),
    }
    for year in summary_years:
        sample[f"probability_{year}"] = probability_at_summary_year(rows, year)
    for key, path, _label in MONTE_CARLO_PARAMETERS:
        sample[key] = config_value(scenario, path)
    return sample


def run_monte_carlo(targets: list[Target], config: dict, baseline_rows: list[dict]) -> dict | None:
    monte_carlo_config = config.get("monte_carlo", {})
    if not monte_carlo_config.get("enabled", False):
        return None

    samples = max(int(monte_carlo_config.get("samples", config.get("monte_carlo_samples", 0))), 0)
    if samples <= 0:
        return None

    summary_years = [int(year) for year in monte_carlo_config.get("summary_years", [])]
    probability_bands = [float(q) for q in monte_carlo_config.get("probability_bands", [0.05, 0.5, 0.95])]
    target_limit = max(int(monte_carlo_config.get("target_limit", len(targets))), 1)
    monte_carlo_targets = targets[: min(target_limit, len(targets))]
    year_step = max(int(monte_carlo_config.get("year_step", config.get("year_step", 1))), 1)
    baseline_config = clone_config(config)
    baseline_config["year_step"] = year_step
    monte_carlo_baseline_rows = arrival_probability_series(monte_carlo_targets, baseline_config)
    rng = random.Random(int(monte_carlo_config.get("seed", config.get("seed", 42))))
    sample_rows: list[dict] = []
    probability_values_by_year = [[] for _row in monte_carlo_baseline_rows]

    for index in range(1, samples + 1):
        scenario = sample_monte_carlo_config(config, rng)
        scenario["year_step"] = year_step
        rows = arrival_probability_series(monte_carlo_targets, scenario)
        sample_rows.append(monte_carlo_sample_row(index, scenario, rows, summary_years))
        for row_index, row in enumerate(rows):
            if row_index < len(probability_values_by_year):
                probability_values_by_year[row_index].append(float(row["probability_at_least_one_signal"]))

    band_rows = []
    for row_index, baseline in enumerate(monte_carlo_baseline_rows):
        values = probability_values_by_year[row_index]
        band = {
            "year": int(baseline["year"]),
            "baseline_probability": float(baseline["probability_at_least_one_signal"]),
        }
        for q in probability_bands:
            band[f"probability_p{int(q * 100):02d}"] = quantile(values, q)
        band_rows.append(band)

    return {
        "samples": samples,
        "target_count": len(monte_carlo_targets),
        "year_step": year_step,
        "summary_years": summary_years,
        "probability_bands": probability_bands,
        "sample_rows": sample_rows,
        "band_rows": band_rows,
        "influence_rows": monte_carlo_influence(sample_rows),
        "representative_rows": representative_monte_carlo_rows(sample_rows),
    }


def selected_timing_distribution(targets: list[Target], config: dict) -> list[dict]:
    scenario = config.get("selected_timing_distribution_scenario", config.get("normal_distribution_scenario", {}))
    bin_size = max(int(scenario["histogram_bin_years"]), 1)
    start = int(config["observation_year_start"])
    end = int(config["observation_year_end"])
    timing_context = build_timing_context(config)
    counts: dict[int, float] = {}

    for year in range(start, end + 1, bin_size):
        density = 0.0
        for target in targets:
            receive_year = year + bin_size / 2
            density += (
                arrival_density_at(receive_year, target, config, timing_context)
                * observability_weight(target, config)
                * observation_epoch_weight(receive_year, target, config)
            )
        counts[year] = density

    total = sum(counts.values()) or 1.0
    return [
        {"year_bin_start": year, "probability_density": count / total}
        for year, count in sorted(counts.items())
    ]


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def points_for_line(rows: list[dict], x_key: str, y_key: str, width: int, height: int, pad: int) -> str:
    xs = [float(r[x_key]) for r in rows]
    ys = [float(r[y_key]) for r in rows]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = 0.0, max(max(ys), 1e-12)
    points = []
    for row in rows:
        x = pad + (float(row[x_key]) - min_x) / (max_x - min_x or 1.0) * (width - 2 * pad)
        y = height - pad - (float(row[y_key]) - min_y) / (max_y - min_y or 1.0) * (height - 2 * pad)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def points_for_line_scaled(
    rows: list[dict],
    x_key: str,
    y_key: str,
    width: int,
    height: int,
    pad: int,
    max_y: float,
) -> str:
    xs = [float(r[x_key]) for r in rows]
    min_x, max_x = min(xs), max(xs)
    points = []
    for row in rows:
        x = pad + (float(row[x_key]) - min_x) / (max_x - min_x or 1.0) * (width - 2 * pad)
        y = height - pad - float(row[y_key]) / (max_y or 1.0) * (height - 2 * pad)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def bars_for_hist(rows: list[dict], width: int, height: int, pad: int) -> str:
    xs = [float(r["year_bin_start"]) for r in rows]
    ys = [float(r["probability_density"]) for r in rows]
    min_x, max_x = min(xs), max(xs)
    max_y = max(max(ys), 1e-12)
    bar_w = max((width - 2 * pad) / max(len(rows), 1), 1.0)
    rects = []
    for row in rows:
        x = pad + (float(row["year_bin_start"]) - min_x) / (max_x - min_x or 1.0) * (width - 2 * pad)
        bar_h = float(row["probability_density"]) / max_y * (height - 2 * pad)
        y = height - pad - bar_h
        rects.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" />'
        )
    return "\n".join(rects)


def monte_carlo_report_section(monte_carlo: dict | None, width: int, height: int, pad: int) -> str:
    if not monte_carlo:
        return ""

    band_rows = monte_carlo["band_rows"]
    sample_rows = monte_carlo["sample_rows"]
    influence_rows = monte_carlo["influence_rows"]
    representative_rows = monte_carlo["representative_rows"]
    peak_probabilities = [float(row["peak_probability"]) for row in sample_rows]
    peak_years = [float(row["peak_year"]) for row in sample_rows]
    curve_areas = [float(row["area_under_probability_curve"]) for row in sample_rows]
    max_y = max(
        max(float(row.get("probability_p95", 0.0)) for row in band_rows),
        max(float(row["baseline_probability"]) for row in band_rows),
        1e-12,
    )
    influence_table = "\n".join(
        f"<tr><td>{row['assumption']}</td><td>{row['rank_correlation']:.3f}</td><td>{row['decile_lift']:.5f}</td></tr>"
        for row in influence_rows[:8]
    )
    representative_table = "\n".join(
        f"<tr><td>{row['case']}</td><td>{row['sample']}</td><td>{row['peak_probability']:.5f}</td><td>{row['peak_year']}</td><td>{row['area_under_probability_curve']:.2f}</td><td>{row['radio_window_years']:.1f}</td><td>{row['max_effective_transmit_power_w']:.2e}</td></tr>"
        for row in representative_rows
    )
    return f"""
  <h2>Monte Carlo uncertainty mode</h2>
  <p>此段使用多參數蒙地卡羅取樣，同時改變 Drake 方程、文明時間尺度、射電窗口、可觀測性與選樣偏差相關參數。它是多參數不確定性探索，不是對外星文明數量的直接預測；v1 固定沿用目前的 timing/window 模型類型，只抽連續參數。</p>
  <section class="metric-row">
    <div class="metric">MC samples<strong>{monte_carlo["samples"]:,}</strong></div>
    <div class="metric">MC target count<strong>{monte_carlo["target_count"]:,}</strong></div>
    <div class="metric">MC year step<strong>{monte_carlo["year_step"]} yr</strong></div>
  </section>
  <section class="metric-row">
    <div class="metric">Peak p50<strong>{quantile(peak_probabilities, 0.50):.4f}</strong></div>
    <div class="metric">Peak year p50<strong>{quantile(peak_years, 0.50):.0f}</strong></div>
    <div class="metric">Max peak probability<strong>{max(peak_probabilities):.4f}</strong></div>
  </section>
  <svg viewBox="0 0 {width} {height}" role="img" aria-label="Monte Carlo probability bands by year">
    <line class="axis" x1="{pad}" y1="{height-pad}" x2="{width-pad}" y2="{height-pad}" />
    <line class="axis" x1="{pad}" y1="{pad}" x2="{pad}" y2="{height-pad}" />
    <polyline class="band-low" points="{points_for_line_scaled(band_rows, "year", "probability_p05", width, height, pad, max_y)}" />
    <polyline class="band-mid" points="{points_for_line_scaled(band_rows, "year", "probability_p50", width, height, pad, max_y)}" />
    <polyline class="band-high" points="{points_for_line_scaled(band_rows, "year", "probability_p95", width, height, pad, max_y)}" />
    <polyline class="line" points="{points_for_line_scaled(band_rows, "year", "baseline_probability", width, height, pad, max_y)}" />
  </svg>
  <p class="caption">Blue = baseline. Green lines show MC p05, p50, and p95 probability bands using the same vertical scale.</p>

  <section class="metric-row">
    <div class="metric">Peak probability p10/p90<strong>{quantile(peak_probabilities, 0.10):.4f} / {quantile(peak_probabilities, 0.90):.4f}</strong></div>
    <div class="metric">Peak year p10/p90<strong>{quantile(peak_years, 0.10):.0f} / {quantile(peak_years, 0.90):.0f}</strong></div>
    <div class="metric">Curve area p50<strong>{quantile(curve_areas, 0.50):.2f}</strong></div>
  </section>

  <h2>Monte Carlo parameter influence</h2>
  <table>
    <thead><tr><th>Parameter</th><th>Rank correlation</th><th>Top-bottom decile lift</th></tr></thead>
    <tbody>{influence_table}</tbody>
  </table>

  <h2>Representative Monte Carlo cases</h2>
  <table>
    <thead><tr><th>Case</th><th>Sample</th><th>Peak probability</th><th>Peak year</th><th>Curve area</th><th>Radio window</th><th>Transmit power</th></tr></thead>
    <tbody>{representative_table}</tbody>
  </table>
"""


def write_html(
    series: list[dict],
    distribution: list[dict],
    targets: list[Target],
    config: dict,
    sensitivity: list[dict],
    monte_carlo: dict | None,
) -> None:
    width, height, pad = 920, 360, 54
    peak_series = max(series, key=lambda r: r["probability_at_least_one_signal"])
    peak_dist = max(distribution, key=lambda r: r["probability_density"])
    avg_distance = mean(t.distance_ly for t in targets)
    civ = config["civilization"]
    timing_model = civ.get("timing_model", "normal")
    window_model = civ.get("radio_window_model", "fixed")
    peak_gap = abs(int(peak_series["year"]) - int(peak_dist["year_bin_start"]))
    communication = config["communication"]
    rigor = config.get("rigor", {})
    sensitivity_rows = "\n".join(
        f"<tr><td>{row['assumption']}</td><td>{row['peak_probability_impact']:.5f}</td><td>{row['peak_year_impact']:.0f} yr</td></tr>"
        for row in sensitivity[:8]
    )
    html = f"""<!doctype html>
<html lang="zh-Hant">
<meta charset="utf-8">
<title>Drake Signal Window Simulation</title>
<style>
  body {{ margin: 0; font-family: Arial, "Noto Sans TC", sans-serif; background: #101418; color: #edf2f4; }}
  main {{ max-width: 1080px; margin: 0 auto; padding: 32px 24px 52px; }}
  h1 {{ font-size: 30px; margin: 0 0 10px; }}
  h2 {{ font-size: 20px; margin: 34px 0 12px; }}
  p, li {{ color: #cbd5dd; line-height: 1.65; }}
  code {{ color: #9bd3ff; }}
  .metric-row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 22px 0; }}
  .metric {{ border: 1px solid #2d3a43; border-radius: 8px; padding: 14px; background: #151c22; }}
  .metric strong {{ display: block; font-size: 22px; color: #ffffff; margin-top: 4px; }}
  svg {{ width: 100%; height: auto; background: #151c22; border: 1px solid #2d3a43; border-radius: 8px; }}
  .axis {{ stroke: #60717d; stroke-width: 1; }}
  .line {{ fill: none; stroke: #57c7ff; stroke-width: 3; }}
  .expected {{ fill: none; stroke: #ffbf69; stroke-width: 2; opacity: .9; }}
  .band-low, .band-mid, .band-high {{ fill: none; stroke: #72dd8a; stroke-width: 2; opacity: .55; }}
  .band-mid {{ stroke-width: 3; opacity: .9; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0 22px; background: #151c22; border: 1px solid #2d3a43; }}
  th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid #2d3a43; color: #dbe5eb; }}
  th {{ color: #ffffff; background: #1b242b; }}
  rect {{ fill: #72dd8a; opacity: .76; }}
  .caption {{ color: #9facb7; font-size: 14px; }}
</style>
<main>
  <h1>德雷克方程與射電通信時間窗口推論</h1>
  <p>此報告由 <code>simulate.py</code> 產生，直接讀取專案根目錄的 <code>data.js</code>。它不是在宣稱外星文明數量，而是把德雷克方程參數、射電通信窗口、光速延遲與既有功率門檻資料組合成可調情境。</p>

  <p>This standalone report uses timing model <code>{timing_model}</code>. Years on the probability curve are Earth receive years; source activity is evaluated at <code>emit_year = receive_year - distance_ly</code>, so light-speed delay is already included.</p>
  <p>The blue curve is the first layer: observable civilizations under a continuous-emission assumption. The orange curve keeps the radio-window synchronization hypothesis and shows how much additional loss is introduced if emissions are finite or intermittent. The normal timing model is retained for comparison, while the default log-normal and gamma options are right-skewed alternatives for multiplicative development factors or prerequisite-accumulation processes.</p>
  <p>Rigor controls are enabled in this run: uncertainty spread <code>{float(rigor.get("uncertainty_spread", 0.0)):.2f}</code>, catalog selection bias <code>{float(rigor.get("catalog_selection_bias", 0.0)):.2f}</code>, beam coverage <code>{float(communication.get("beam_coverage", 1.0)):.2f}</code>, duty cycle <code>{float(communication.get("duty_cycle", 1.0)):.2f}</code>, frequency coverage <code>{float(communication.get("frequency_coverage", 1.0)):.2f}</code>, and assumption correlation <code>{float(rigor.get("assumption_correlation", 0.0)):.2f}</code>.</p>

  <section class="metric-row">
    <div class="metric">使用候選目標<strong>{len(targets):,}</strong></div>
    <div class="metric">平均距離<strong>{avg_distance:,.0f} ly</strong></div>
    <div class="metric">最高年度接收機率<strong>{peak_series["probability_at_least_one_signal"]:.3f}</strong></div>
  </section>

  <h2>地球接收到至少一個射電訊號的機率對時間</h2>
  <svg viewBox="0 0 {width} {height}" role="img" aria-label="Signal probability by year">
    <line class="axis" x1="{pad}" y1="{height-pad}" x2="{width-pad}" y2="{height-pad}" />
    <line class="axis" x1="{pad}" y1="{pad}" x2="{pad}" y2="{height-pad}" />
    <polyline class="line" points="{points_for_line(series, "year", "probability_at_least_one_signal", width, height, pad)}" />
    <polyline class="expected" points="{points_for_line(series, "year", "window_limited_probability", width, height, pad)}" />
  </svg>
  <p class="caption">藍線為至少一個訊號抵達的年度機率；橘線為期望可偵測來源數，兩者各自正規化到圖面高度。峰值年份約為 {peak_series["year"]}。</p>

  <h2>所選時間模型下的最可能接收年份分布</h2>
  <svg viewBox="0 0 {width} {height}" role="img" aria-label="Most likely arrival-year distribution">
    <line class="axis" x1="{pad}" y1="{height-pad}" x2="{width-pad}" y2="{height-pad}" />
    <line class="axis" x1="{pad}" y1="{pad}" x2="{pad}" y2="{height-pad}" />
    {bars_for_hist(distribution, width, height, pad)}
  </svg>
  <p class="caption">直方圖使用目前選取的文明時間模型，而不是強制用常態分佈作第一展示。最高密度區間起點約為 {peak_dist["year_bin_start"]}。</p>

{monte_carlo_report_section(monte_carlo, width, height, pad)}

  <h2>物理模型與學術背景推導 (Physical Modeling & Academic Background)</h2>
  <div style="background: #151c22; border: 1px solid #2d3a43; border-radius: 8px; padding: 18px; margin: 18px 0; font-size: 15px;">
    <h3 style="color: #57c7ff; margin-top: 0;">1. 能量常數 K 與最低可觀測通量 F<sub>min</sub></h3>
    <p>所需等效全向發射功率（EIRP）計算公式為：<code>P_required = K * d_ly^2</code>，其中 <code>K = 1.12 &times; 10<sup>11</sup> W/ly<sup>2</sup></code>。</p>
    <p>由物理關係 <code>P = 4&pi; &times; d<sup>2</sup> &times; F<sub>min</sub></code> 換算（1 ly &approx; 9.4607 &times; 10<sup>15</sup> m），可推導出對應的最低可偵測通量門檻：</p>
    <p style="text-align: center; font-family: monospace; color: #9bd3ff;">F<sub>min</sub> = K / (4&pi; &times; (9.4607 &times; 10<sup>15</sup>)<sup>2</sup>) &approx; 10<sup>-22</sup> W/m<sup>2</sup></p>
    <p>這在射電 SETI 中代表一個 Jansky 等級的高靈敏度接收極限。例如，望遠鏡在 1.4 GHz (L-band) 的系統等效通量密度（SEFD）為 2 Jy 時，在 10 kHz 頻寬、300 秒積分時間與 S/N = 10 門檻下，其可偵測通量極限正好落在 10<sup>-22</sup> W/m<sup>2</sup> 的量級。</p>

    <h3 style="color: #57c7ff;">2. 空間匹配半徑 0.2&deg;</h3>
    <p>在與 Breakthrough Listen 進行觀測匹配時，設定天球夾角 &le; 0.2&deg;（12 角分）。這對應於 L-band (1.4 GHz) 下主流單口徑望遠鏡（如 Parkes 的 14' = 0.23&deg; 或 GBT 的 9' = 0.15&deg;）的半功率波束寬度（HPBW），確保目標系外行星位於望遠鏡觀測的半功率波束視場（FOV）內。</p>

    <h3 style="color: #57c7ff;">3. 卡爾達肖夫尺度 (Kardashev Scale)</h3>
    <p>發射功率分級對應卡爾達肖夫尺度：<code>K_scale = (log10(P) - 6) / 10</code>：</p>
    <ul>
      <li>地球級：P &le; 10<sup>14</sup> W (K_scale &le; 0.8)</li>
      <li>I 型文明：P &le; 10<sup>16</sup> W (K_scale &le; 1.0)</li>
      <li>星際通信級：P &le; 10<sup>20</sup> W (K_scale &le; 1.4，介於 I 型與 II 型之間的過渡狀態)</li>
      <li>II 型以上：P &gt; 10<sup>20</sup> W (K_scale &gt; 1.4)</li>
    </ul>

    <h3 style="color: #57c7ff;">4. 假說耦合模型 (Hypothesis Coupling)</h3>
    <p>模擬生命發生率 f<sub>l</sub> 與智慧生命率 f<sub>i</sub> 的關聯，反映生命與智慧是否有共同演化瓶頸的學術假說：</p>
    <ul>
      <li><strong>Independent (獨立模型)</strong>: f<sub>l</sub> 與 f<sub>i</sub> 完全獨立抽樣。</li>
      <li><strong>Weakly Coupled (弱耦合)</strong>: f<sub>i</sub>' = f<sub>i</sub> * (f<sub>l</sub> / 0.1)<sup>0.5</sup></li>
      <li><strong>Strongly Coupled (強耦合)</strong>: f<sub>i</sub>' = f<sub>i</sub> * (f<sub>l</sub> / 0.1)</li>
      <li><strong>Bottleneck (演化瓶頸)</strong>: f<sub>i</sub>' 強制限制在 [0.001, 0.01]。</li>
      <li><strong>Rare Intelligence (稀有智慧)</strong>: f<sub>l</sub>' = f<sub>l</sub> * 1.5 且 f<sub>i</sub>' = f<sub>i</sub> * 0.001。</li>
    </ul>

    <h3 style="color: #57c7ff;">5. 雙重生命尺度 (Dual Timescales)</h3>
    <p>將德雷克文明壽命 L 拆分為先驗強度 <code>lPrior</code>（用於確定文明曾經存在的總機率）與時間發射窗 <code>tActive + tLeakage</code>（用於計算訊號在空間中的波前寬度），避免重疊計算並支持「文明雖亡，信號仍在」的傳播場景。</p>

    <h3 style="color: #57c7ff;">6. 星表選擇偏誤 (Selection Bias)</h3>
    <p>星表完整度由 logistic 機率函數模擬：<code>p_catalog = sigmoid(2.5 - selectionBias * 0.02 * d + 2.0 * q)</code>，其中 d 為距離，q 為行星資料品質評分。此函數量化了因觀測限制對遠距離與低質量目標的篩選偏差。</p>
  </div>

  <h2>可調參數</h2>
  <p>請編輯 <code>config.json</code> 來改變德雷克方程項、文明誕生時間、發展時間、射電窗口長度、發射功率能力與模擬樣本數。重新執行腳本後，<code>outputs/</code> 內的 CSV 與 HTML 會更新。</p>
</main>
</html>
"""
    (OUTPUT_DIR / "report.html").write_text(html, encoding="utf-8")


def main() -> None:
    config = load_config()
    OUTPUT_DIR.mkdir(exist_ok=True)
    targets = load_targets(int(config.get("max_catalog_targets", 0)) or None)
    series = arrival_probability_series(targets, config)
    series = add_uncertainty_band(targets, config, series)
    distribution = selected_timing_distribution(targets, config)
    sensitivity = sensitivity_ranking(targets, config, series)
    monte_carlo = run_monte_carlo(targets, config, series)

    write_csv(OUTPUT_DIR / "arrival_probability_by_year.csv", series)
    write_csv(OUTPUT_DIR / "selected_timing_arrival_year_distribution.csv", distribution)
    write_csv(OUTPUT_DIR / "sensitivity_ranking.csv", sensitivity)
    if monte_carlo:
        write_csv(OUTPUT_DIR / "monte_carlo_samples.csv", monte_carlo["sample_rows"])
        write_csv(OUTPUT_DIR / "monte_carlo_probability_bands.csv", monte_carlo["band_rows"])
    write_html(series, distribution, targets, config, sensitivity, monte_carlo)

    peak_series = max(series, key=lambda r: r["probability_at_least_one_signal"])
    peak_dist = max(distribution, key=lambda r: r["probability_density"])
    print(f"Targets: {len(targets)}")
    print(f"Peak annual reception probability: {peak_series['probability_at_least_one_signal']:.4f} in {peak_series['year']}")
    print(f"Most likely selected-timing arrival bin starts at: {peak_dist['year_bin_start']}")
    if monte_carlo:
        print(f"Monte Carlo samples: {monte_carlo['samples']}")
    print(f"Wrote: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
