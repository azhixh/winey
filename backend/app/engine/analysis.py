"""
Central beverage analysis service orchestrating normalization, composition calculations,
dataset scoring, and evidence-backed health evaluations.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from app.engine.normalization import (
    NormalizedBeverageData,
    normalize_beverage_input,
)
from app.engine.composition import (
    ETHANOL_DENSITY_G_ML,
    calculate_alcohol_grams,
    calculate_sugar_per_serving,
    calculate_energy_per_100ml,
    calculate_sugar_concentration_per_100ml,
)
from app.engine.composition_scoring import (
    CompositionScoringEngine,
    CompositionScoreResult,
)
from app.engine.health_assessment import (
    HealthAssessmentEngine,
    HealthAssessmentResult,
)


@dataclass
class AvailableCalculations:
    """
    Container for deterministic calculations and their units.
    """
    alcohol_grams: Optional[float] = None
    alcohol_grams_unit: str = "g"
    ethanol_density_used_g_ml: float = ETHANOL_DENSITY_G_ML

    sugar_per_serving_g: Optional[float] = None
    sugar_per_serving_unit: str = "g"

    energy_per_100ml_kcal: Optional[float] = None
    energy_per_100ml_unit: str = "kcal/100 mL"

    sugar_concentration_g_per_100ml: Optional[float] = None
    sugar_concentration_unit: str = "g/100 mL"

    explanations: list[str] = field(default_factory=list)


@dataclass
class BeverageAnalysisResult:
    """
    Complete analysis result produced by BeverageAnalysisService.
    """
    status: str
    normalized_input: NormalizedBeverageData
    calculations: AvailableCalculations
    composition_comparison: CompositionScoreResult
    health_assessment: HealthAssessmentResult
    warnings: list[str]
    sources: list[dict[str, Any]]


class BeverageAnalysisService:
    """
    High-level service orchestrating beverage profile analysis.
    """

    def __init__(
        self,
        composition_scoring_engine: Optional[CompositionScoringEngine] = None,
        health_assessment_engine: Optional[HealthAssessmentEngine] = None,
    ):
        self.composition_scoring_engine = composition_scoring_engine or CompositionScoringEngine()
        self.health_assessment_engine = health_assessment_engine or HealthAssessmentEngine()

    def analyze(
        self,
        beverage_type: Any,
        serving_size: float,
        serving_size_unit: str = "ml",
        sugar: Optional[float] = None,
        sugar_unit: str = "g",
        sugar_concentration_g_per_100ml: Optional[float] = None,
        calories: Optional[float] = None,
        calories_unit: str = "kcal",
        sodium: Optional[float] = None,
        sodium_unit: str = "mg",
        caffeine: Optional[float] = None,
        caffeine_unit: str = "mg",
        alcohol_percentage: Optional[float] = None,
        alcohol_unit: str = "%",
    ) -> BeverageAnalysisResult:
        """
        Execute full beverage analysis pipeline:
        1. Normalize units and validate inputs.
        2. Perform physical and concentration calculations.
        3. Evaluate composition against reference benchmark (requiring >= 100 records).
        4. Evaluate health rules against authoritative evidence.
        5. Compile warnings, notices, and source citations.
        """
        # 1. Normalize input
        norm_data = normalize_beverage_input(
            beverage_type=beverage_type,
            serving_size=serving_size,
            serving_size_unit=serving_size_unit,
            sugar=sugar,
            sugar_unit=sugar_unit,
            sugar_concentration_g_per_100ml=sugar_concentration_g_per_100ml,
            calories=calories,
            calories_unit=calories_unit,
            sodium=sodium,
            sodium_unit=sodium_unit,
            caffeine=caffeine,
            caffeine_unit=caffeine_unit,
            alcohol_percentage=alcohol_percentage,
            alcohol_unit=alcohol_unit,
        )

        calc_explanations: list[str] = []

        # 2. Composition Calculations
        # 2a. Alcohol grams
        alc_grams, alc_expl = calculate_alcohol_grams(
            serving_size_ml=norm_data.serving_size_ml,
            alcohol_percentage=norm_data.alcohol_percentage,
            density_g_ml=ETHANOL_DENSITY_G_ML,
        )
        if alc_expl:
            calc_explanations.append(alc_expl)

        # 2b. Sugar per serving & sugar concentration per 100 mL
        sugar_conc = norm_data.sugar_concentration_g_per_100ml
        sugar_serving = norm_data.sugar_g

        if sugar_serving is not None and sugar_conc is None:
            conc_calc, _ = calculate_sugar_concentration_per_100ml(
                sugar_g_per_serving=sugar_serving,
                serving_size_ml=norm_data.serving_size_ml,
            )
            sugar_conc = conc_calc
        elif sugar_conc is not None and sugar_serving is None:
            sugar_calc, _ = calculate_sugar_per_serving(
                sugar_concentration_g_per_100ml=sugar_conc,
                serving_size_ml=norm_data.serving_size_ml,
            )
            sugar_serving = sugar_calc

        if sugar_serving is None and sugar_conc is None:
            calc_explanations.append("Sugar metrics omitted: neither sugar per serving nor sugar concentration was provided.")

        # 2c. Energy per 100 mL
        energy_100ml, energy_expl = calculate_energy_per_100ml(
            energy_per_serving_kcal=norm_data.calories,
            serving_size_ml=norm_data.serving_size_ml,
        )
        if energy_expl:
            calc_explanations.append(energy_expl)

        calculations = AvailableCalculations(
            alcohol_grams=alc_grams,
            alcohol_grams_unit="g",
            ethanol_density_used_g_ml=ETHANOL_DENSITY_G_ML,
            sugar_per_serving_g=sugar_serving,
            sugar_per_serving_unit="g",
            energy_per_100ml_kcal=energy_100ml,
            energy_per_100ml_unit="kcal/100 mL",
            sugar_concentration_g_per_100ml=sugar_conc,
            sugar_concentration_unit="g/100 mL",
            explanations=calc_explanations,
        )

        # Update normalized data with derived concentration if needed
        norm_data.sugar_concentration_g_per_100ml = sugar_conc

        # 3. Composition Scoring & Comparison
        comp_result = self.composition_scoring_engine.evaluate(
            beverage=norm_data,
            metric_name="sugar_concentration_g_per_100ml",
        )

        # 4. Evidence-Grounded Health Assessment
        health_result = self.health_assessment_engine.evaluate(norm_data)

        # 5. Compile Global Warnings
        compiled_warnings: list[str] = [
            "composition_score and health_impact_score remain null pending integration with validated datasets and evidence-backed evaluation rules."
        ]

        # Missing input warnings
        missing_inputs: list[str] = []
        for name, val in [
            ("sugar_g", norm_data.sugar_g),
            ("calories", norm_data.calories),
            ("sodium_mg", norm_data.sodium_mg),
            ("caffeine_mg", norm_data.caffeine_mg),
            ("alcohol_percentage", norm_data.alcohol_percentage),
        ]:
            if val is None:
                missing_inputs.append(name)

        if missing_inputs:
            compiled_warnings.append(
                f"Optional composition metric(s) [{', '.join(missing_inputs)}] were omitted and preserved as null; no default values were assumed."
            )

        if alc_grams is not None:
            compiled_warnings.append(
                f"Calculated alcohol mass: {alc_grams} g based on {norm_data.alcohol_percentage}% ABV, "
                f"{norm_data.serving_size_ml} mL serving size, and ethanol density of {ETHANOL_DENSITY_G_ML} g/mL."
            )
        else:
            compiled_warnings.append("Alcohol percentage was not provided; alcohol gram calculation omitted.")

        # Append health advisories and warnings
        for adv in health_result.advisories:
            compiled_warnings.append(adv.get("advisory_message", ""))

        for hw in health_result.warnings:
            if hw not in compiled_warnings:
                compiled_warnings.append(hw)

        # Collect sources
        all_sources: list[dict[str, Any]] = list(health_result.sources)
        if comp_result.benchmark_name:
            all_sources.append({
                "benchmark_name": comp_result.benchmark_name,
                "version": comp_result.dataset_version,
                "sample_size": comp_result.sample_size,
                "method": comp_result.calculation_method,
            })

        return BeverageAnalysisResult(
            status="success",
            normalized_input=norm_data,
            calculations=calculations,
            composition_comparison=comp_result,
            health_assessment=health_result,
            warnings=compiled_warnings,
            sources=all_sources,
        )
