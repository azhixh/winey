"""
PRD Section 12 Deterministic Scoring Engine.

Pure, independently testable functions implementing:
1. Normalization (serving size, units, ethanol mass, standard drinks, benzoic acid factor 0.848, null preservation).
2. Benchmark classification (lower_than_typical, typical, higher_than_typical, very_high).
3. Guideline ratio and exact piecewise 5-band subscore curve (r <= 0.5: 100; 0.5 < r <= 1: 100->60; 1 < r <= 2: 60->20; 2 < r <= 3: 20->0; r > 3: 0).
4. Separate Health Impact Score and Composition Score.
5. Critical overrides (methanol, acute caffeine; caps Health Impact Score at 40 with red banner).
6. Personalization scaling (body weight mg/kg, under-18 3 mg/kg, pregnancy caffeine 200 mg, alcohol avoid messages).
7. Confidence calculation (High >= 80%, Medium 60-79%, Low < 60% with 'Partial analysis').
8. Complete traceability to rules_version and dataset_version.
"""

import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any, Literal


# =====================================================================
# Configuration Loaders
# =====================================================================

DEFAULT_RULES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "rules.json"
DEFAULT_BENCHMARKS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "reference_ranges.json"


def load_rules(path: Optional[Path] = None) -> dict[str, Any]:
    """Load configuration rules from rules.json."""
    rules_file = Path(path) if path else DEFAULT_RULES_PATH
    if not rules_file.exists():
        raise FileNotFoundError(f"Rules configuration file not found at {rules_file}")
    return json.loads(rules_file.read_text(encoding="utf-8"))


def load_reference_ranges(path: Optional[Path] = None) -> dict[str, Any]:
    """Load reference benchmark distributions from reference_ranges.json."""
    ranges_file = Path(path) if path else DEFAULT_BENCHMARKS_PATH
    if not ranges_file.exists():
        raise FileNotFoundError(f"Reference ranges file not found at {ranges_file}")
    return json.loads(ranges_file.read_text(encoding="utf-8"))


# =====================================================================
# Data Transfer / Parameter Objects
# =====================================================================

@dataclass
class UserProfile:
    """User personal profile for limit scaling."""
    age_group: Literal["adult", "under_18"] = "adult"
    weight_kg: float = 60.0
    is_pregnant_or_breastfeeding: bool = False
    has_diabetes: bool = False
    has_heart_condition: bool = False
    regulator_region: str = "WHO"
    standard_drink_definition_g: float = 10.0


@dataclass
class IngredientSubscoreResult:
    """Individual guideline ingredient subscore and ratio evaluation."""
    ingredient_key: str
    ingredient_name: str
    amount_per_serving: float
    amount_per_100ml: Optional[float]
    unit: str
    guideline_limit: float
    guideline_ratio: float
    band: str
    subscore: float
    daily_limit: Optional[float] = None
    daily_share: Optional[float] = None
    is_critical_breach: bool = False
    source_organization: str = ""
    source_url: str = ""
    publication_year: Optional[int] = None
    rationale: str = ""


@dataclass
class IngredientBenchmarkResult:
    """Individual benchmark percentile classification."""
    ingredient_key: str
    amount_evaluated: float
    unit: str
    status: str                         # 'lower_than_typical', 'typical', 'higher_than_typical', 'very_high', 'limited_benchmark_data'
    credit: Optional[float]             # 100, 60, 50, 20 or None
    percentile_band: Optional[str]
    sample_size: int
    is_sufficient: bool
    risk_direction: str


@dataclass
class CriticalOverrideInfo:
    """Critical override state and banner information."""
    is_critical: bool = False
    capped_score: Optional[float] = None
    uncapped_score: Optional[float] = None
    banner_color: Optional[str] = None
    critical_reasons: list[str] = field(default_factory=list)


@dataclass
class ScoringEngineResult:
    """Full outcome of PRD Section 12 scoring pipeline."""
    beverage_type: str
    serving_size_ml: float
    product_name: Optional[str]

    # Scores
    health_impact_score: Optional[float]
    uncapped_health_impact_score: Optional[float]
    composition_score: Optional[float]

    # Evaluations
    guideline_evaluations: list[IngredientSubscoreResult]
    benchmark_evaluations: list[IngredientBenchmarkResult]

    # Alcohol metrics
    alcohol_grams: Optional[float]
    standard_drinks: Optional[float]
    alcohol_advisory: Optional[str]

    # Status & Flags
    critical_override: CriticalOverrideInfo
    confidence_level: str               # 'High', 'Medium', 'Low'
    confidence_percentage: float
    is_partial_analysis: bool

    # Highlights
    higher_than_typical: list[str]
    lower_than_typical: list[str]
    missing_fields: list[str]
    warnings: list[str]
    disclaimer: str

    # Versions
    rules_version: str
    dataset_version: str

    # Wine ML integration
    wine_model: Optional[dict[str, Any]] = None


# =====================================================================
# Pure Calculation Functions
# =====================================================================

def calculate_alcohol_grams(
    serving_ml: float,
    abv_percent: Optional[float],
    ethanol_density: float = 0.789,
) -> Optional[float]:
    """Calculate alcohol mass in grams: volume * (ABV / 100) * 0.789."""
    if abv_percent is None or serving_ml <= 0.0:
        return None
    grams = serving_ml * (abv_percent / 100.0) * ethanol_density
    return round(grams, 2)


def calculate_standard_drinks(
    alcohol_grams: Optional[float],
    standard_drink_g: float = 10.0,
) -> Optional[float]:
    """Calculate number of standard drinks based on pure alcohol grams."""
    if alcohol_grams is None or standard_drink_g <= 0.0:
        return None
    drinks = alcohol_grams / standard_drink_g
    return round(drinks, 1)


def convert_sodium_benzoate_to_benzoic_acid(
    sodium_benzoate_mg: Optional[float],
    conversion_factor: float = 0.848,
) -> Optional[float]:
    """Convert sodium benzoate mass to benzoic acid equivalent using factor 0.848."""
    if sodium_benzoate_mg is None:
        return None
    return round(sodium_benzoate_mg * conversion_factor, 3)


def calculate_guideline_ratio(
    amount_per_serving: float,
    applicable_limit: float,
) -> float:
    """Calculate ratio r = amount_per_serving / applicable_limit."""
    if applicable_limit <= 0.0:
        raise ValueError("applicable_limit must be strictly positive.")
    return round(amount_per_serving / applicable_limit, 4)


def calculate_subscore_from_ratio(ratio: float) -> tuple[float, str]:
    """
    Exact piecewise scoring curve from PRD Section 12.4:
    - r <= 0.5: Favourable, 100
    - 0.5 < r <= 1.0: Moderate, Linear 100 to 60 (100 - (r - 0.5) * 80)
    - 1.0 < r <= 2.0: Caution, Linear 60 to 20 (60 - (r - 1.0) * 40)
    - 2.0 < r <= 3.0: High, Linear 20 to 0 (20 - (r - 2.0) * 20)
    - r > 3.0: High, 0
    """
    if ratio < 0.0:
        raise ValueError("ratio cannot be negative.")

    # Floating point tolerance
    eps = 1e-9

    if ratio <= 0.5 + eps:
        return 100.0, "Favourable"
    elif ratio <= 1.0 + eps:
        # Linear from 100 to 60: slope = (60 - 100) / (1.0 - 0.5) = -40 / 0.5 = -80
        score = 100.0 - (ratio - 0.5) * 80.0
        return round(max(60.0, min(100.0, score)), 2), "Moderate"
    elif ratio <= 2.0 + eps:
        # Linear from 60 to 20: slope = (20 - 60) / (2.0 - 1.0) = -40 / 1.0 = -40
        score = 60.0 - (ratio - 1.0) * 40.0
        return round(max(20.0, min(60.0, score)), 2), "Caution"
    elif ratio <= 3.0 + eps:
        # Linear from 20 to 0: slope = (0 - 20) / (3.0 - 2.0) = -20 / 1.0 = -20
        score = 20.0 - (ratio - 2.0) * 20.0
        return round(max(0.0, min(20.0, score)), 2), "High"
    else:
        return 0.0, "High"


def classify_benchmark_percentile(
    amount_per_100ml: float,
    distribution: dict[str, Any],
) -> tuple[str, Optional[str]]:
    """
    Classify value against benchmark percentiles:
    - Lower than typical: below P25
    - Typical: P25 through P75 (inclusive)
    - Higher than typical: above P75 through P95 (inclusive)
    - Very high: above P95

    Returns:
        (status_key, band_label)
    """
    p = distribution.get("percentiles", {})
    p25 = p.get("p25")
    p75 = p.get("p75")
    p95 = p.get("p95")

    if p25 is None or p75 is None or p95 is None:
        return "limited_benchmark_data", None

    if amount_per_100ml < p25:
        return "lower_than_typical", "< P25"
    elif amount_per_100ml <= p75:
        return "typical", "P25 - P75"
    elif amount_per_100ml <= p95:
        return "higher_than_typical", "P75 - P95"
    else:
        return "very_high", "> P95"


def calculate_composition_credit(
    benchmark_status: str,
    risk_direction: str,
    credits_config: dict[str, Any],
) -> Optional[float]:
    """
    Calculate composition credit from PRD Section 12.7:
    - Typical: 100
    - Lower than typical: 100 if high_is_bad, otherwise 60
    - Higher than typical: 50 if high_is_bad, otherwise 100
    - Very high: 20 if high_is_bad, otherwise 0
    - Info-only / limited-data: None
    """
    if benchmark_status == "limited_benchmark_data" or risk_direction in ("info_only", "reference_only"):
        return None

    is_high_bad = (risk_direction == "high_is_bad")

    if benchmark_status == "typical":
        return float(credits_config.get("typical", 100.0))
    elif benchmark_status == "lower_than_typical":
        cfg = credits_config.get("lower_than_typical", {})
        return float(cfg.get("high_is_bad", 100.0) if is_high_bad else cfg.get("other", 60.0))
    elif benchmark_status == "higher_than_typical":
        cfg = credits_config.get("higher_than_typical", {})
        return float(cfg.get("high_is_bad", 50.0) if is_high_bad else cfg.get("other", 100.0))
    elif benchmark_status == "very_high":
        cfg = credits_config.get("very_high", {})
        return float(cfg.get("high_is_bad", 20.0) if is_high_bad else cfg.get("other", 0.0))

    return None


def calculate_confidence(
    filled_weighted_count: int,
    total_weighted_count: int,
    confidence_config: dict[str, Any],
) -> tuple[str, float, bool]:
    """
    Calculate confidence level based on proportion of weighted fields supplied:
    - High: >= 80%
    - Medium: 60% to < 80%
    - Low: < 60% (labelled 'Partial analysis')

    Returns:
        (confidence_level, percentage, is_partial_analysis)
    """
    if total_weighted_count <= 0:
        return "Low", 0.0, True

    ratio = filled_weighted_count / total_weighted_count
    pct = round(ratio * 100.0, 1)

    high_th = float(confidence_config.get("high_threshold", 0.80))
    med_th = float(confidence_config.get("medium_threshold", 0.60))

    if ratio >= high_th:
        return "High", pct, False
    elif ratio >= med_th:
        return "Medium", pct, False
    else:
        return "Low", pct, True


# =====================================================================
# Main Engine Orchestrator
# =====================================================================

class BQASScoringEngine:
    """
    Orchestrates the PRD Section 12 scoring pipeline.
    """

    def __init__(
        self,
        rules_path: Optional[Path] = None,
        benchmarks_path: Optional[Path] = None,
    ):
        self.rules = load_rules(rules_path)
        self.benchmarks = load_reference_ranges(benchmarks_path)
        self.rules_version = self.rules.get("rules_version", "1.0.0")
        self.dataset_version = self.benchmarks.get("dataset_version", "1.0.0")

    def evaluate_beverage(
        self,
        beverage_type: str,
        serving_size_ml: float,
        inputs: dict[str, Any],
        profile: Optional[UserProfile] = None,
        product_name: Optional[str] = None,
        wine_color: Optional[str] = None,  # 'red' or 'white'
    ) -> ScoringEngineResult:
        """
        Execute full deterministic analysis for a beverage entry.
        """
        user_prof = profile or UserProfile()
        warnings: list[str] = []

        if serving_size_ml <= 0.0:
            raise ValueError("Serving size (ml) must be strictly positive.")
        if serving_size_ml > 5000.0:
            warnings.append(f"Implausible serving size ({serving_size_ml} mL) exceeds 5,000 mL.")

        # 1. Alcohol grams & standard drinks
        abv = inputs.get("alcohol")
        alcohol_grams = calculate_alcohol_grams(
            serving_ml=serving_size_ml,
            abv_percent=abv,
            ethanol_density=self.rules.get("general_constants", {}).get("ethanol_density_g_ml", 0.789),
        )
        std_drinks = calculate_standard_drinks(
            alcohol_grams=alcohol_grams,
            standard_drink_g=user_prof.standard_drink_definition_g,
        )

        alcohol_advisory: Optional[str] = None
        is_alcoholic_type = beverage_type in ("Beer", "Wine", "Alcohol", "Spirits") or (abv is not None and abv > 0.0)
        if is_alcoholic_type:
            alcohol_advisory = self.rules.get("guideline_rules", {}).get("alcohol", {}).get("who_statement")
            if user_prof.age_group == "under_18" or user_prof.is_pregnant_or_breastfeeding:
                warnings.append("Health Advisory: Alcohol consumption is strongly contraindicated for minors and during pregnancy/breastfeeding.")

        # 2. Evaluate Guideline Rules
        guideline_results: list[IngredientSubscoreResult] = []
        critical_flags: list[str] = []

        # 2a. Sugars
        sugars_val = inputs.get("sugars")
        if sugars_val is not None and sugars_val >= 0.0:
            # Check unit: if user provided per 100ml, convert to serving
            unit_in = inputs.get("sugars_unit", "g")
            if unit_in == "g/100ml":
                sugars_serving = sugars_val * (serving_size_ml / 100.0)
                sugars_100ml = sugars_val
            else:
                sugars_serving = sugars_val
                sugars_100ml = sugars_val * (100.0 / serving_size_ml)

            sugar_rule = self.rules["guideline_rules"]["sugars"]
            ideal_target = sugar_rule["ideal_target_g_day"]     # 25.0
            cap_limit = sugar_rule["cap_limit_g_day"]           # 50.0

            ratio = calculate_guideline_ratio(sugars_serving, ideal_target)
            subscore, band = calculate_subscore_from_ratio(ratio)

            guideline_results.append(
                IngredientSubscoreResult(
                    ingredient_key="sugars",
                    ingredient_name=sugar_rule["name"],
                    amount_per_serving=round(sugars_serving, 2),
                    amount_per_100ml=round(sugars_100ml, 2),
                    unit="g",
                    guideline_limit=ideal_target,
                    guideline_ratio=ratio,
                    band=band,
                    subscore=subscore,
                    daily_limit=cap_limit,
                    daily_share=round(sugars_serving / cap_limit, 4),
                    source_organization=sugar_rule["source_organization"],
                    source_url=sugar_rule["source_url"],
                    publication_year=sugar_rule.get("publication_year"),
                    rationale=sugar_rule["rationale"],
                )
            )

        # 2b. Caffeine
        caffeine_val = inputs.get("caffeine")
        if caffeine_val is not None and caffeine_val >= 0.0:
            unit_in = inputs.get("caffeine_unit", "mg")
            if unit_in == "mg/100ml":
                caffeine_serving = caffeine_val * (serving_size_ml / 100.0)
                caffeine_100ml = caffeine_val
            else:
                caffeine_serving = caffeine_val
                caffeine_100ml = caffeine_val * (100.0 / serving_size_ml)

            caf_rule = self.rules["guideline_rules"]["caffeine"]

            # Personalization limits
            if user_prof.age_group == "under_18":
                daily_limit = caf_rule["daily_limit_under_18_mg_per_kg"] * user_prof.weight_kg
                single_dose_limit = daily_limit  # Under-18 single dose reference equals daily threshold
                ratio = calculate_guideline_ratio(caffeine_serving, single_dose_limit)
                daily_share = round(caffeine_serving / daily_limit, 4)
            elif user_prof.is_pregnant_or_breastfeeding:
                daily_limit = caf_rule["daily_limit_pregnant_mg"]
                single_dose_limit = daily_limit
                ratio = calculate_guideline_ratio(caffeine_serving, single_dose_limit)
                daily_share = round(caffeine_serving / daily_limit, 4)
            else:
                single_dose_limit = caf_rule["single_dose_limit_adult_mg"]   # 200 mg
                daily_limit = caf_rule["daily_limit_adult_mg"]               # 400 mg
                ratio = calculate_guideline_ratio(caffeine_serving, single_dose_limit)
                daily_share = round(caffeine_serving / daily_limit, 4)

            subscore, band = calculate_subscore_from_ratio(ratio)

            # Check critical override: caffeine serving exceeds single dose limit
            is_critical = caffeine_serving > single_dose_limit
            if is_critical:
                critical_flags.append(
                    f"Caffeine content ({round(caffeine_serving, 1)} mg) exceeds safe single-dose boundary "
                    f"({round(single_dose_limit, 1)} mg) for {user_prof.age_group} profile."
                )

            guideline_results.append(
                IngredientSubscoreResult(
                    ingredient_key="caffeine",
                    ingredient_name=caf_rule["name"],
                    amount_per_serving=round(caffeine_serving, 2),
                    amount_per_100ml=round(caffeine_100ml, 2),
                    unit="mg",
                    guideline_limit=round(single_dose_limit, 2),
                    guideline_ratio=ratio,
                    band=band,
                    subscore=subscore,
                    daily_limit=round(daily_limit, 2),
                    daily_share=daily_share,
                    is_critical_breach=is_critical,
                    source_organization=caf_rule["source_organization"],
                    source_url=caf_rule["source_url"],
                    publication_year=caf_rule.get("publication_year"),
                    rationale=caf_rule["rationale"],
                )
            )

        # 2c. Sodium Benzoate (E211)
        benzoate_val = inputs.get("sodium_benzoate")
        if benzoate_val is not None and benzoate_val >= 0.0:
            # benzoate in mg/L -> compute mg in serving
            benzoate_serving_mg = benzoate_val * (serving_size_ml / 1000.0)
            benzoate_rule = self.rules["guideline_rules"]["sodium_benzoate"]
            factor = benzoate_rule["conversion_factor_to_benzoic_acid"]
            benzoic_acid_mg = convert_sodium_benzoate_to_benzoic_acid(benzoate_serving_mg, factor) or 0.0

            adi_limit = benzoate_rule["adi_mg_per_kg_body_weight"] * user_prof.weight_kg
            ratio = calculate_guideline_ratio(benzoic_acid_mg, adi_limit)
            subscore, band = calculate_subscore_from_ratio(ratio)

            guideline_results.append(
                IngredientSubscoreResult(
                    ingredient_key="sodium_benzoate",
                    ingredient_name=benzoate_rule["name"],
                    amount_per_serving=round(benzoate_serving_mg, 2),
                    amount_per_100ml=round(benzoate_serving_mg * 100.0 / serving_size_ml, 2),
                    unit="mg/L",
                    guideline_limit=round(adi_limit, 2),
                    guideline_ratio=ratio,
                    band=band,
                    subscore=subscore,
                    daily_limit=round(adi_limit, 2),
                    daily_share=round(benzoic_acid_mg / adi_limit, 4),
                    source_organization=benzoate_rule["source_organization"],
                    source_url=benzoate_rule["source_url"],
                    publication_year=benzoate_rule.get("publication_year"),
                    rationale=benzoate_rule["rationale"],
                )
            )

        # 2d. Sulphites
        sulphites_val = inputs.get("sulphites")
        if sulphites_val is not None and sulphites_val >= 0.0:
            # sulphites in mg/L -> compute mg in serving
            sulphites_serving_mg = sulphites_val * (serving_size_ml / 1000.0)
            sulphite_rule = self.rules["guideline_rules"]["sulphites"]
            adi_limit = sulphite_rule["adi_mg_per_kg_body_weight"] * user_prof.weight_kg
            ratio = calculate_guideline_ratio(sulphites_serving_mg, adi_limit)
            subscore, band = calculate_subscore_from_ratio(ratio)

            guideline_results.append(
                IngredientSubscoreResult(
                    ingredient_key="sulphites",
                    ingredient_name=sulphite_rule["name"],
                    amount_per_serving=round(sulphites_serving_mg, 2),
                    amount_per_100ml=round(sulphites_serving_mg * 100.0 / serving_size_ml, 2),
                    unit="mg/L",
                    guideline_limit=round(adi_limit, 2),
                    guideline_ratio=ratio,
                    band=band,
                    subscore=subscore,
                    daily_limit=round(adi_limit, 2),
                    daily_share=round(sulphites_serving_mg / adi_limit, 4),
                    source_organization=sulphite_rule["source_organization"],
                    source_url=sulphite_rule["source_url"],
                    publication_year=sulphite_rule.get("publication_year"),
                    rationale=sulphite_rule["rationale"],
                )
            )

        # 2e. Sodium
        sodium_val = inputs.get("sodium")
        if sodium_val is not None and sodium_val >= 0.0:
            unit_in = inputs.get("sodium_unit", "mg")
            if unit_in == "mg/100ml":
                sodium_serving = sodium_val * (serving_size_ml / 100.0)
                sodium_100ml = sodium_val
            else:
                sodium_serving = sodium_val
                sodium_100ml = sodium_val * (100.0 / serving_size_ml)

            sodium_rule = self.rules["guideline_rules"]["sodium"]
            daily_limit = sodium_rule["daily_limit_adult_mg"]  # 2000 mg
            # For sodium, single-serving ratio evaluated against daily budget share
            ratio = calculate_guideline_ratio(sodium_serving, daily_limit)
            subscore, band = calculate_subscore_from_ratio(ratio)

            guideline_results.append(
                IngredientSubscoreResult(
                    ingredient_key="sodium",
                    ingredient_name=sodium_rule["name"],
                    amount_per_serving=round(sodium_serving, 2),
                    amount_per_100ml=round(sodium_100ml, 2),
                    unit="mg",
                    guideline_limit=daily_limit,
                    guideline_ratio=ratio,
                    band=band,
                    subscore=subscore,
                    daily_limit=daily_limit,
                    daily_share=round(sodium_serving / daily_limit, 4),
                    source_organization=sodium_rule["source_organization"],
                    source_url=sodium_rule["source_url"],
                    publication_year=sodium_rule.get("publication_year"),
                    rationale=sodium_rule["rationale"],
                )
            )

        # 2f. Methanol (Critical Rule)
        methanol_val = inputs.get("methanol")
        if methanol_val is not None and methanol_val >= 0.0:
            # methanol in g per L of pure alcohol
            methanol_rule = self.rules["guideline_rules"]["methanol"]
            max_limit = methanol_rule["max_limit_g_per_l_pure_alcohol"]  # 10.0
            ratio = calculate_guideline_ratio(methanol_val, max_limit)
            subscore, band = calculate_subscore_from_ratio(ratio)

            is_critical = methanol_val > max_limit
            if is_critical:
                critical_flags.append(
                    f"Methanol level ({methanol_val} g/L pure alcohol) exceeds maximum legal threshold ({max_limit} g/L). "
                    "CRITICAL TOXICOLOGICAL RISK."
                )

            guideline_results.append(
                IngredientSubscoreResult(
                    ingredient_key="methanol",
                    ingredient_name=methanol_rule["name"],
                    amount_per_serving=round(methanol_val, 2),
                    amount_per_100ml=None,
                    unit="g/L pure alcohol",
                    guideline_limit=max_limit,
                    guideline_ratio=ratio,
                    band=band,
                    subscore=subscore,
                    is_critical_breach=is_critical,
                    source_organization=methanol_rule["source_organization"],
                    source_url=methanol_rule["source_url"],
                    publication_year=methanol_rule.get("publication_year"),
                    rationale=methanol_rule["rationale"],
                )
            )

        # 3. Calculate Health Impact Score
        raw_health_score: Optional[float] = None
        if guideline_results:
            total_weight = 0.0
            weighted_sum = 0.0
            for gr in guideline_results:
                rule_cfg = self.rules["guideline_rules"].get(gr.ingredient_key, {})
                w = float(rule_cfg.get("weight", 1.0))
                weighted_sum += gr.subscore * w
                total_weight += w

            if total_weight > 0.0:
                raw_health_score = round(weighted_sum / total_weight, 1)

        # 4. Critical Overrides Application
        override_cfg = self.rules.get("critical_override", {})
        capped_threshold = float(override_cfg.get("capped_health_impact_score", 40.0))
        is_critical = len(critical_flags) > 0

        final_health_score: Optional[float] = raw_health_score
        if is_critical and raw_health_score is not None:
            final_health_score = min(raw_health_score, capped_threshold)

        critical_info = CriticalOverrideInfo(
            is_critical=is_critical,
            capped_score=final_health_score if is_critical else None,
            uncapped_score=raw_health_score,
            banner_color=override_cfg.get("banner_color", "red") if is_critical else None,
            critical_reasons=critical_flags,
        )

        # 5. Evaluate Benchmark Percentiles & Composition Credits
        benchmark_results: list[IngredientBenchmarkResult] = []
        higher_than_typical: list[str] = []
        lower_than_typical: list[str] = []

        category_key = beverage_type
        if beverage_type == "Wine":
            color = (wine_color or inputs.get("wine_type", "red")).strip().lower()
            category_key = f"Wine_{color}"

        cat_benchmarks = self.benchmarks.get("categories", {}).get(category_key, {})

        composition_credits: list[float] = []

        # Map candidate benchmark metrics
        for metric_name, dist in cat_benchmarks.items():
            val = inputs.get(metric_name)
            if val is not None and val >= 0.0:
                unit_in = inputs.get(f"{metric_name}_unit", dist.get("unit", ""))
                # Normalize to per 100ml if serving was given
                if "100" in dist.get("unit", "") and unit_in in ("g", "mg", "kcal"):
                    val_100ml = val * (100.0 / serving_size_ml)
                else:
                    val_100ml = val

                sample_size = dist.get("sample_size", 0)
                is_sufficient = sample_size >= self.rules.get("general_constants", {}).get("minimum_benchmark_samples", 100)

                rule_cfg = self.rules["guideline_rules"].get(metric_name, {})
                risk_dir = rule_cfg.get("risk_direction", "high_is_bad")

                status, band_label = classify_benchmark_percentile(val_100ml, dist)
                credit = calculate_composition_credit(status, risk_dir, self.rules.get("composition_credits", {}))

                if credit is not None:
                    composition_credits.append(credit)

                if status == "higher_than_typical" or status == "very_high":
                    higher_than_typical.append(f"{metric_name.capitalize()} is higher than typical category levels ({val_100ml:.1f} {dist.get('unit')}).")
                elif status == "lower_than_typical":
                    lower_than_typical.append(f"{metric_name.capitalize()} is lower than typical category levels ({val_100ml:.1f} {dist.get('unit')}).")

                benchmark_results.append(
                    IngredientBenchmarkResult(
                        ingredient_key=metric_name,
                        amount_evaluated=round(val_100ml, 2),
                        unit=dist.get("unit", ""),
                        status=status,
                        credit=credit,
                        percentile_band=band_label,
                        sample_size=sample_size,
                        is_sufficient=is_sufficient,
                        risk_direction=risk_dir,
                    )
                )

        composition_score: Optional[float] = None
        if composition_credits:
            composition_score = round(sum(composition_credits) / len(composition_credits), 1)

        # 6. Confidence & Partial Analysis
        # Count filled weighted guideline fields out of supported fields for this drink
        category_weighted_fields = {
            "Soft drink": ["sugars", "caffeine", "sodium_benzoate", "sodium"],
            "Energy drink": ["caffeine", "sugars", "sodium", "taurine"],
            "Beer": ["alcohol", "sulphites", "carbohydrates", "energy"],
            "Wine": ["alcohol", "sulphites", "residual_sugar", "pH"],
            "Alcohol": ["alcohol", "methanol"],
            "Spirits": ["alcohol", "methanol"],
        }.get(beverage_type, ["sugars", "caffeine", "alcohol", "sodium"])

        filled_weighted = [f for f in category_weighted_fields if inputs.get(f) is not None]
        missing_fields = [f for f in category_weighted_fields if inputs.get(f) is None]

        conf_level, conf_pct, is_partial = calculate_confidence(
            len(filled_weighted),
            len(category_weighted_fields),
            self.rules.get("confidence_levels", {}),
        )

        # 7. Wine ML Sensory Quality Evaluation (UCI Portuguese Vinho Verde model)
        wine_model_info: Optional[dict[str, Any]] = None
        if beverage_type == "Wine":
            from app.engine.wine_quality import (
                WineQualityModelService,
                REGIONAL_APPLICABILITY_NOTE,
            )
            # 11 UCI features mapping
            required_uci_features = [
                "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
                "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide", "density",
                "pH", "sulphates", "alcohol",
            ]
            provided_uci = [f for f in required_uci_features if inputs.get(f) is not None]
            missing_uci = [f for f in required_uci_features if inputs.get(f) is None]

            color = (wine_color or inputs.get("wine_type", "red")).strip().lower()
            if color not in ("red", "white"):
                color = "red"

            wine_service = WineQualityModelService()
            test_mae = None
            try:
                card = wine_service.get_model_card()
                test_mae = card.get("models", {}).get(color, {}).get("metrics", {}).get("test_mae")
            except Exception:
                test_mae = None

            if len(missing_uci) == 0:
                # All 11 inputs supplied
                try:
                    pred_res = wine_service.predict(color, {f: float(inputs[f]) for f in required_uci_features})
                    wine_model_info = {
                        "is_available": True,
                        "predicted_quality": pred_res.get("quality_score"),
                        "predicted_rating": pred_res.get("quality_rating"),
                        "reason_if_unavailable": None,
                        "test_mae": test_mae or pred_res.get("model_metrics", {}).get("test_mae"),
                        "model_limitations": REGIONAL_APPLICABILITY_NOTE,
                        "disclaimer": (
                            "Empirical machine-learning prediction based on expert panel ratings from Portuguese "
                            "Vinho Verde wines (Cortez et al., 2009). Completely separated from health impact evaluation."
                        ),
                    }
                except Exception as e:
                    wine_model_info = {
                        "is_available": False,
                        "predicted_quality": None,
                        "predicted_rating": None,
                        "reason_if_unavailable": f"Model inference error: {str(e)}",
                        "test_mae": test_mae,
                        "model_limitations": REGIONAL_APPLICABILITY_NOTE,
                        "disclaimer": REGIONAL_APPLICABILITY_NOTE,
                    }
            else:
                wine_model_info = {
                    "is_available": False,
                    "predicted_quality": None,
                    "predicted_rating": None,
                    "reason_if_unavailable": (
                        f"Wine quality prediction requires all 11 physicochemical inputs. "
                        f"Missing inputs: {', '.join(missing_uci)}."
                    ),
                    "test_mae": test_mae,
                    "model_limitations": REGIONAL_APPLICABILITY_NOTE,
                    "disclaimer": (
                        "The UCI model predicts sensory quality for Portuguese Vinho Verde samples and may not generalize "
                        "to other wines. Wine sensory prediction is strictly separated from health impact scoring."
                    ),
                }

        disclaimer = (
            "For informational and educational purposes only. BQAS reports do not constitute medical, clinical, "
            "or regulatory advice. Results depend on user-entered values and reference datasets that may contain errors."
        )

        return ScoringEngineResult(
            beverage_type=beverage_type,
            serving_size_ml=serving_size_ml,
            product_name=product_name,
            health_impact_score=final_health_score,
            uncapped_health_impact_score=raw_health_score,
            composition_score=composition_score,
            guideline_evaluations=guideline_results,
            benchmark_evaluations=benchmark_results,
            alcohol_grams=alcohol_grams,
            standard_drinks=std_drinks,
            alcohol_advisory=alcohol_advisory,
            critical_override=critical_info,
            confidence_level=conf_level,
            confidence_percentage=conf_pct,
            is_partial_analysis=is_partial,
            higher_than_typical=higher_than_typical,
            lower_than_typical=lower_than_typical,
            missing_fields=missing_fields,
            warnings=warnings,
            disclaimer=disclaimer,
            rules_version=self.rules_version,
            dataset_version=self.dataset_version,
            wine_model=wine_model_info,
        )



# Singleton engine instance
_default_engine: Optional[BQASScoringEngine] = None


def get_scoring_engine() -> BQASScoringEngine:
    """Return default singleton BQASScoringEngine instance."""
    global _default_engine
    if _default_engine is None:
        _default_engine = BQASScoringEngine()
    return _default_engine
