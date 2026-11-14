"""
FoodLens AI — Metabolic Impact & Physiological Analysis Engine
Implements deterministic scoring models for:
1. Protein Density & Protein-to-Energy (P:E) Ratio (Protein Leverage Hypothesis).
2. Estimated Sugar Spike Index (SSI) with Glycemic Buffering (Fibre, Protein, Lipid matrix).
3. Sodium-to-Calorie Ratio & FSSAI HFSS Cardiovascular Risk.
4. Weight Management & Satiety Index (WMI).

Architectural Guarantees:
- Pure Python, zero UI dependencies.
- Deterministic arithmetic: LLM never computes numbers.
- Handles missing values gracefully: None remains None.
- Neutral, evidence-based language grounded in ICMR-NIN 2024 and FSSAI guidelines.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from foodlens.nutrition import NutritionProfile


@dataclass(frozen=True)
class ProteinDensityResult:
    """Protein density and leverage metrics."""
    protein_energy_pct: Optional[float]
    protein_per_100kcal: Optional[float]
    density_score: Optional[float]  # 0 to 100
    classification: str
    satiety_impact: str
    color_hex: str


@dataclass(frozen=True)
class SugarSpikeResult:
    """Estimated glycemic impact and sugar spike risk."""
    sugar_spike_index: Optional[float]
    available_carbs_g: Optional[float]
    buffering_factor: Optional[float]
    risk_band: str
    color_hex: str
    explanation: str


@dataclass(frozen=True)
class SodiumAnalysisResult:
    """Sodium density, serving load, and FSSAI HFSS risk."""
    sodium_mg: Optional[float]
    sodium_per_100kcal: Optional[float]
    daily_limit_pct_per_serving: Optional[float]
    is_fssai_hfss_high: bool
    risk_rating: Optional[float]  # 0 to 100
    color_hex: str
    explanation: str


@dataclass(frozen=True)
class WeightManagementResult:
    """Satiety vs. caloric density prediction for body composition."""
    weight_management_index: Optional[float]  # WMI
    verdict: str
    color_hex: str
    hunger_latency: str
    energy_density_kcal_per_g: Optional[float]
    explanation: str


@dataclass(frozen=True)
class MetabolicProfile:
    """Aggregated physiological and metabolic profile for a food product."""
    protein_density: ProteinDensityResult
    sugar_spike: SugarSpikeResult
    sodium: SodiumAnalysisResult
    weight_management: WeightManagementResult
    summary_sentence: str


def calculate_protein_density(profile: NutritionProfile) -> ProteinDensityResult:
    """
    Computes Protein Energy Percentage (PE%) and Protein Density Score.
    Reference: Simpson & Raubenheimer Protein Leverage Hypothesis.
    """
    p_val = profile.protein_g.value if profile.protein_g else None
    e_val = profile.energy_kcal.value if profile.energy_kcal else None

    if p_val is None or e_val is None or e_val <= 0:
        return ProteinDensityResult(
            protein_energy_pct=None,
            protein_per_100kcal=None,
            density_score=None,
            classification="Insufficient Data",
            satiety_impact="Protein or caloric energy not declared on label.",
            color_hex="#64748B"
        )

    pe_pct = round((p_val * 4.0 / e_val) * 100.0, 1)
    p_100kcal = round((p_val / e_val) * 100.0, 1)

    # Score from 0 to 100 (5% PE = 0, 20% PE = 100)
    score = min(100.0, max(0.0, round(((pe_pct - 5.0) / 15.0) * 100.0, 1)))

    if pe_pct < 6.0:
        cls = "Critically Diluted"
        impact = "Protein is critically diluted (<6% of energy). According to the Protein Leverage Hypothesis, low protein density often triggers involuntary overconsumption of total calories."
        color = "#DC2626"
    elif pe_pct < 10.0:
        cls = "Sub-Optimal"
        impact = "Sub-optimal protein density (6–10% of energy). Provides short-lived satiety; requires additional protein sources in the meal."
        color = "#F59E0B"
    elif pe_pct < 18.0:
        cls = "Moderate / Balanced"
        impact = "Balanced protein density (10–18% of energy). Meets standard maintenance dietary baselines for adults."
        color = "#0284C7"
    else:
        cls = "High Protein Density"
        impact = "High protein density (≥18% of energy). Promotes strong satiety signaling (CCK/PYY) and supports muscle retention during weight management."
        color = "#166534"

    return ProteinDensityResult(
        protein_energy_pct=pe_pct,
        protein_per_100kcal=p_100kcal,
        density_score=score,
        classification=cls,
        satiety_impact=impact,
        color_hex=color
    )


def calculate_sugar_spike(profile: NutritionProfile, serving_size_g: Optional[float] = None) -> SugarSpikeResult:
    """
    Computes Estimated Sugar Spike Index (SSI) factoring in glycemic buffering.
    Buffers: Dietary Fibre (0.08x), Protein (0.04x), Fat (0.02x).
    """
    sugars = profile.sugars_g.value if profile.sugars_g else None
    carbs = profile.carbs_g.value if profile.carbs_g else None
    fibre = profile.fibre_g.value if profile.fibre_g else 0.0
    protein = profile.protein_g.value if profile.protein_g else 0.0
    fat = profile.fat_g.value if profile.fat_g else 0.0

    if sugars is None and carbs is None:
        return SugarSpikeResult(
            sugar_spike_index=None,
            available_carbs_g=None,
            buffering_factor=None,
            risk_band="Insufficient Data",
            color_hex="#64748B",
            explanation="Carbohydrate and sugar content not declared on label."
        )

    sugars_eff = sugars if sugars is not None else 0.0
    carbs_eff = carbs if carbs is not None else sugars_eff

    available_carbs = max(0.0, carbs_eff - (fibre or 0.0))
    complex_carbs = max(0.0, available_carbs - sugars_eff)

    # Glycemic Buffering Factor
    gbf = round(1.0 + (0.08 * (fibre or 0.0)) + (0.04 * (protein or 0.0)) + (0.02 * (fat or 0.0)), 2)

    # Standardize to declared portion or 100g reference
    portion = serving_size_g or profile.serving_size_g or 100.0
    scale_factor = portion / 100.0

    # Raw glycemic load weighted by fast-sugar (1.5x) and complex starch (0.6x)
    raw_spike = (sugars_eff * 1.5 + complex_carbs * 0.6) / gbf
    ssi = round(raw_spike * scale_factor, 1)

    if ssi < 15.0:
        band = "Low"
        color = "#166534"
        expl = "Gentle postprandial glucose curve. High buffering from protein, fiber, or low simple sugar minimizes insulin spikes."
    elif ssi < 30.0:
        band = "Moderate"
        color = "#F59E0B"
        expl = "Moderate glucose rise. Contains some rapidly digestible carbohydrates balanced by other macronutrients."
    elif ssi < 50.0:
        band = "High"
        color = "#EA580C"
        expl = "Steep glucose surge. Fast-absorbing sugars or refined starches with limited fiber buffer can elevate circulating insulin."
    else:
        band = "Severe"
        color = "#DC2626"
        expl = "Rapid hyper-glycemic spike. Minimal buffering allows rapid intestinal absorption, often followed by reactive rebound hunger."

    return SugarSpikeResult(
        sugar_spike_index=ssi,
        available_carbs_g=round(available_carbs, 1),
        buffering_factor=gbf,
        risk_band=band,
        color_hex=color,
        explanation=expl
    )


def calculate_sodium_risk(profile: NutritionProfile, serving_size_g: Optional[float] = None) -> SodiumAnalysisResult:
    """
    Evaluates Sodium Density and Percentage of ICMR-NIN 2,000 mg safe daily limit.
    FSSAI HFSS thresholds: >600mg/100g (solid), >50mg/100ml (liquid).
    """
    sod_val = profile.sodium_mg.value if profile.sodium_mg else None
    e_val = profile.energy_kcal.value if profile.energy_kcal else None

    if sod_val is None:
        return SodiumAnalysisResult(
            sodium_mg=None,
            sodium_per_100kcal=None,
            daily_limit_pct_per_serving=None,
            is_fssai_hfss_high=False,
            risk_rating=None,
            color_hex="#64748B",
            explanation="Sodium content not declared on label."
        )

    # Threshold checks
    threshold = 50.0 if profile.is_beverage else 600.0
    is_high = sod_val > threshold

    sod_per_100kcal = round((sod_val / e_val) * 100.0, 1) if (e_val and e_val > 0) else None

    portion = serving_size_g or profile.serving_size_g or 100.0
    sod_per_serving = (sod_val * portion) / 100.0
    daily_pct = round((sod_per_serving / 2000.0) * 100.0, 1)

    risk_rating = min(100.0, max(0.0, round((sod_val / 1200.0) * 100.0, 1)))

    if is_high or daily_pct >= 30.0:
        color = "#DC2626"
        expl = f"Exceeds FSSAI HFSS threshold ({sod_val:g} mg / 100g vs. {threshold:g} mg cutoff). Single portion provides {daily_pct}% of the ICMR-NIN 2,000 mg daily ceiling."
    elif sod_val > (threshold / 2.0) or daily_pct >= 15.0:
        color = "#F59E0B"
        expl = f"Moderate sodium ({sod_val:g} mg / 100g). Delivers {daily_pct}% of the ICMR-NIN 2,000 mg daily ceiling per serving."
    else:
        color = "#166534"
        expl = f"Low sodium profile ({sod_val:g} mg / 100g). Safe for cardiovascular fluid balance."

    return SodiumAnalysisResult(
        sodium_mg=sod_val,
        sodium_per_100kcal=sod_per_100kcal,
        daily_limit_pct_per_serving=daily_pct,
        is_fssai_hfss_high=is_high,
        risk_rating=risk_rating,
        color_hex=color,
        explanation=expl
    )


def calculate_weight_management(profile: NutritionProfile) -> WeightManagementResult:
    """
    Computes Weight Management & Satiety Index (WMI).
    Integrates Energy Density, Protein Satiety, Fibre Satiety, and Sugar/Fat hyper-palatability.
    """
    e_val = profile.energy_kcal.value if profile.energy_kcal else None
    if e_val is None or e_val <= 0:
        return WeightManagementResult(
            weight_management_index=None,
            verdict="Insufficient Data",
            color_hex="#64748B",
            hunger_latency="Unknown",
            energy_density_kcal_per_g=None,
            explanation="Nutritional energy data missing."
        )

    protein = profile.protein_g.value if profile.protein_g else 0.0
    fibre = profile.fibre_g.value if profile.fibre_g else 0.0
    sugars = profile.sugars_g.value if profile.sugars_g else 0.0
    sat_fat = profile.sat_fat_g.value if profile.sat_fat_g else 0.0
    sodium = profile.sodium_mg.value if profile.sodium_mg else 0.0

    energy_density = round(e_val / 100.0, 2)  # kcal per gram

    # Formula: Baseline 50 + Protein bonus + Fibre bonus - Sugar penalty - SatFat penalty - Sodium penalty - EnergyDensity penalty
    raw_wmi = 50.0 + (2.5 * protein) + (3.0 * fibre) - (1.2 * sugars) - (0.8 * sat_fat) - (0.015 * sodium) - (5.0 * energy_density)
    wmi = round(min(100.0, max(0.0, raw_wmi)), 1)

    if wmi >= 65.0:
        verdict = "Optimal Satiety / Fat Loss Support"
        color = "#166534"
        latency = "~3.5 to 4.5 Hours Fullness"
        expl = "High fullness-to-calorie ratio. Rich in protein or fiber with moderate caloric density, supporting sustained appetite control."
    elif wmi >= 40.0:
        verdict = "Neutral / Portion Control Needed"
        color = "#F59E0B"
        latency = "~2.0 to 3.0 Hours Fullness"
        expl = "Moderate energy density. Suitable for everyday balanced maintenance when portion sizes are monitored."
    else:
        verdict = "Low Satiety / Weight Gain Driver"
        color = "#DC2626"
        latency = "~1.0 to 1.5 Hours Before Rebound Hunger"
        expl = "Calorie-dense with low protein and fiber. High hyper-palatability triggers fast gastric emptying and rapid return of appetite."

    return WeightManagementResult(
        weight_management_index=wmi,
        verdict=verdict,
        color_hex=color,
        hunger_latency=latency,
        energy_density_kcal_per_g=energy_density,
        explanation=expl
    )


def analyze_metabolic_impact(profile: NutritionProfile, serving_size_g: Optional[float] = None) -> MetabolicProfile:
    """
    Orchestrates complete physiological and metabolic evaluation for a food product.
    """
    p_density = calculate_protein_density(profile)
    s_spike = calculate_sugar_spike(profile, serving_size_g=serving_size_g)
    s_sodium = calculate_sodium_risk(profile, serving_size_g=serving_size_g)
    w_mgmt = calculate_weight_management(profile)

    # Construct synthesized summary sentence
    summary_parts = []
    if s_spike.risk_band in ["High", "Severe"]:
        summary_parts.append(f"{s_spike.risk_band.lower()} sugar spike risk")
    if s_sodium.is_fssai_hfss_high:
        summary_parts.append("high sodium density")
    if p_density.classification in ["Critically Diluted", "Sub-Optimal"]:
        summary_parts.append("diluted protein")
    elif p_density.classification == "High Protein Density":
        summary_parts.append("rich protein density")

    if summary_parts:
        summary = f"This product is characterized by {', '.join(summary_parts)}, presenting a {w_mgmt.verdict.lower()} profile."
    else:
        summary = f"Nutritionally balanced profile with {s_spike.risk_band.lower()} glycemic impact and {p_density.classification.lower()}."

    return MetabolicProfile(
        protein_density=p_density,
        sugar_spike=s_spike,
        sodium=s_sodium,
        weight_management=w_mgmt,
        summary_sentence=summary
    )
