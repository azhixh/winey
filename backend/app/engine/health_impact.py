"""
Health impact rules interface and evidence-grounded assessment engine.

Strict scientific constraints:
- Every active health rule includes: source URL, publication year, applicable beverage types, units, and rationale.
- Never invents medical thresholds, acceptable daily intakes (ADI), or safety cutoffs.
- Never classifies a beverage as 'safe' or 'healthy' based on incomplete data.
- Leaves health_impact_score strictly null (None) because no authoritative composite health score exists.
- Provides explicit, non-medical advisories for known hazards (e.g., WHO statement on alcohol).
- Evaluates rule applicability strictly against beverage type and available metrics.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from app.engine.normalization import NormalizedBeverageData
from app.schemas import BeverageType


@dataclass
class HealthRule:
    """
    Authoritative, evidence-backed health rule definition.
    """
    rule_id: str
    title: str
    source_name: str
    source_url: str
    publication_year: int
    applicable_beverage_types: list[str]
    units: str
    rationale: str
    active: bool = True

    def is_applicable_to(self, beverage_type: str) -> bool:
        """Check whether the rule is applicable to the given beverage type."""
        if not self.active:
            return False
        if "all" in [t.lower() for t in self.applicable_beverage_types]:
            return True
        return beverage_type.strip().lower() in [t.lower() for t in self.applicable_beverage_types]


@dataclass
class HealthRuleEvaluation:
    """
    Result of evaluating an authoritative health rule against beverage data.
    """
    rule_id: str
    title: str
    source_name: str
    source_url: str
    publication_year: int
    applicable: bool
    triggered: bool
    units: str
    rationale: str
    advisory_message: str


@dataclass
class HealthAssessmentResult:
    """
    Structured outcome of health impact rules evaluation.
    Health score remains strictly null (None).
    """
    health_impact_score: Optional[float] = None
    status: str = "unavailable"
    advisories: list[HealthRuleEvaluation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)


# =====================================================================
# Authoritative Evidence-Grounded Rules
# =====================================================================

WHO_ALCOHOL_RULE = HealthRule(
    rule_id="WHO_ALCOHOL_2023",
    title="WHO Statement on Alcohol Consumption and Health Risks",
    source_name="World Health Organization (WHO) Regional Office for Europe",
    source_url="https://www.who.int/europe/news/item/04-01-2023-no-level-of-alcohol-consumption-is-safe-for-our-health",
    publication_year=2023,
    applicable_beverage_types=["Beer", "Wine", "Spirits"],
    units="% ABV / g ethanol",
    rationale=(
        "According to the World Health Organization (2023), there is no evidence of a threshold "
        "at which the carcinogenic and health risks of alcohol consumption are absent; "
        "no level of alcohol consumption is risk-free for health."
    ),
    active=True,
)


class HealthImpactEngine:
    """
    Evaluates beverage nutritional and chemical profile against authoritative, documented health rules.

    Guarantees:
    - Never generates a composite numeric health score without an internationally recognized standard.
    - Never marks a beverage as safe or healthy when inputs are incomplete.
    - Rejects unsupported or inactive rules from generating any health classification.
    """

    def __init__(self, rules: Optional[list[HealthRule]] = None):
        if rules is None:
            self.rules = [WHO_ALCOHOL_RULE]
        else:
            self.rules = rules

    def evaluate(self, beverage: NormalizedBeverageData) -> HealthAssessmentResult:
        """
        Evaluate applicable health rules for a normalized beverage.
        """
        advisories: list[HealthRuleEvaluation] = []
        warnings: list[str] = [
            "health_impact_score remains null: No validated composite health scoring rubric exists or has been implemented.",
            "Health impact evaluations provide non-medical, observational references only and must not be interpreted as clinical diagnoses."
        ]
        sources: list[dict[str, Any]] = []

        bev_type_str = beverage.beverage_type.value if isinstance(beverage.beverage_type, BeverageType) else str(beverage.beverage_type)

        # 1. Incomplete Data Guard: Check if key metrics are missing
        missing_fields: list[str] = []
        for name, val in [
            ("sugar", beverage.sugar_g),
            ("calories", beverage.calories),
            ("sodium", beverage.sodium_mg),
            ("caffeine", beverage.caffeine_mg),
            ("alcohol_percentage", beverage.alcohol_percentage),
        ]:
            if val is None:
                missing_fields.append(name)

        if missing_fields:
            warnings.append(
                f"Nutritional inputs for [{', '.join(missing_fields)}] are missing. "
                "Beverage cannot be classified as safe or healthy based on incomplete nutritional profile."
            )

        # 2. Evaluate Registered Authoritative Rules
        for rule in self.rules:
            # Check applicability to this beverage type
            if not rule.is_applicable_to(bev_type_str):
                # Ensure unsupported rules never produce a health classification or triggered advisory
                continue

            # Special evaluation for WHO alcohol rule
            if rule.rule_id == "WHO_ALCOHOL_2023":
                is_alcoholic_category = bev_type_str in ["Beer", "Wine", "Spirits"]
                has_alcohol = (beverage.alcohol_percentage is not None and beverage.alcohol_percentage > 0.0)

                if is_alcoholic_category or has_alcohol:
                    advisory = (
                        "Health Advisory (WHO 2023): No level of alcohol consumption is risk-free for health. "
                        "Alcohol is a toxic, psychoactive, and group 1 carcinogen linked to various cancers and cardiovascular conditions."
                    )
                    eval_res = HealthRuleEvaluation(
                        rule_id=rule.rule_id,
                        title=rule.title,
                        source_name=rule.source_name,
                        source_url=rule.source_url,
                        publication_year=rule.publication_year,
                        applicable=True,
                        triggered=True,
                        units=rule.units,
                        rationale=rule.rationale,
                        advisory_message=advisory,
                    )
                    advisories.append(eval_res)
                    sources.append({
                        "rule_id": rule.rule_id,
                        "source_name": rule.source_name,
                        "source_url": rule.source_url,
                        "publication_year": rule.publication_year,
                        "rationale": rule.rationale,
                    })

        return HealthAssessmentResult(
            health_impact_score=None,
            status="unavailable",
            advisories=advisories,
            warnings=warnings,
            sources=sources,
        )
