"""
Health assessment engine for BQAS.

Scientific and regulatory principles:
- Kept completely separate from composition scoring.
- For non-alcoholic beverages: reports only evidence-backed observations based on available data.
- Handles missing nutrients explicitly with missing-data notices.
- Refuses to label a beverage as healthy, unhealthy, or safe from incomplete data.
- For alcoholic beverages: never provides product rankings, quality recommendations, or consumption optimization.
  Provides factual health-risk information and appropriate warnings only.
- Never creates an arbitrary composite numeric health score (health_impact_score is strictly None).
- Explicit statuses: 'available', 'insufficient_data', 'not_evaluated'.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from app.engine.normalization import NormalizedBeverageData
from app.engine.evidence_registry import EvidenceRegistry, EvidenceObservation


@dataclass
class HealthAssessmentResult:
    """
    Outcome of an evidence-backed health assessment.
    Health score remains strictly None.
    """
    status: str                                    # 'available', 'insufficient_data', 'not_evaluated'
    health_impact_score: Optional[float] = None    # Strictly None
    observations: list[dict[str, Any]] = field(default_factory=list)
    advisories: list[dict[str, Any]] = field(default_factory=list)
    missing_data_notices: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


class HealthAssessmentEngine:
    """
    Engine evaluating health implications using the EvidenceRegistry.
    """

    def __init__(self, registry: Optional[EvidenceRegistry] = None):
        self.registry = registry or EvidenceRegistry()

    def evaluate(self, beverage: NormalizedBeverageData) -> HealthAssessmentResult:
        """
        Evaluate health evidence and observations for a normalized beverage profile.
        """
        bev_type = beverage.beverage_type.value
        is_alcoholic = bev_type in ["Beer", "Wine", "Spirits"] or (
            beverage.alcohol_percentage is not None and beverage.alcohol_percentage > 0.0
        )

        observations: list[dict[str, Any]] = []
        advisories: list[dict[str, Any]] = []
        sources: list[dict[str, Any]] = []
        warnings: list[str] = []
        missing_notices: list[str] = []
        limitations: list[str] = [
            "Observations reflect published scientific consensus and regulatory guidelines.",
            "Health assessments are non-clinical, informational evaluations and must not be used as medical advice.",
            "Composite health impact scores are intentionally omitted to avoid ungrounded health claims.",
        ]

        # 1. Identify missing nutrient data
        missing_fields = []
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
            notice = (
                f"Nutrient values for [{', '.join(missing_fields)}] are missing. "
                "Beverage cannot be classified as healthy, unhealthy, or safe based on incomplete nutritional profile and data."
            )
            missing_notices.append(notice)
            warnings.append(notice)

        # 2. Alcoholic Beverage Handling
        if is_alcoholic:
            # Strictly provide factual health-risk information only.
            # No product rankings, quality recommendations, or consumption optimization.
            limitations.append(
                "Alcoholic beverage analysis strictly excludes quality rankings, product recommendations, or consumption optimization."
            )
            warnings.append(
                "Alcoholic beverage policy: Quality rankings and consumption recommendations are disabled. "
                "Only factual health-risk warnings are provided."
            )

            # Query active rules for alcoholic beverages
            active_rules = self.registry.get_active_rules(bev_type)
            for rule in active_rules:
                if rule.evaluator:
                    eval_res = rule.evaluator(beverage)
                    if eval_res:
                        obs_entry = {
                            "rule_id": rule.rule_id,
                            "title": rule.title,
                            "source_organization": rule.source_organization,
                            "source_url": rule.source_url,
                            "publication_year": rule.publication_year,
                            "jurisdiction": rule.jurisdiction,
                            "relevant_units": rule.relevant_units,
                            "observation_text": eval_res["observation_text"],
                            "rationale": rule.rationale,
                        }
                        observations.append(obs_entry)
                        advisories.append({
                            "rule_id": rule.rule_id,
                            "title": rule.title,
                            "advisory_message": eval_res["observation_text"],
                            "source_url": rule.source_url,
                        })
                        sources.append({
                            "rule_id": rule.rule_id,
                            "source_organization": rule.source_organization,
                            "source_url": rule.source_url,
                            "publication_year": rule.publication_year,
                            "jurisdiction": rule.jurisdiction,
                        })

            return HealthAssessmentResult(
                status="available",
                health_impact_score=None,
                observations=observations,
                advisories=advisories,
                missing_data_notices=missing_notices,
                warnings=warnings,
                sources=sources,
                limitations=limitations,
            )

        # 3. Non-Alcoholic Beverage Handling
        # If major nutritional indicators (sugar and calories) are missing, status is 'insufficient_data'
        if beverage.sugar_g is None and beverage.calories is None and beverage.sugar_concentration_g_per_100ml is None:
            warnings.append("Insufficient data: Both sugar and calorie metrics are missing. Comprehensive health assessment cannot be performed.")
            return HealthAssessmentResult(
                status="insufficient_data",
                health_impact_score=None,
                observations=[],
                advisories=[],
                missing_data_notices=missing_notices,
                warnings=warnings,
                sources=[],
                limitations=limitations,
            )

        # Evaluate active rules for non-alcoholic category
        active_rules = self.registry.get_active_rules(bev_type)
        for rule in active_rules:
            if rule.evaluator:
                eval_res = rule.evaluator(beverage)
                if eval_res:
                    obs_entry = {
                        "rule_id": rule.rule_id,
                        "title": rule.title,
                        "source_organization": rule.source_organization,
                        "source_url": rule.source_url,
                        "publication_year": rule.publication_year,
                        "jurisdiction": rule.jurisdiction,
                        "relevant_units": rule.relevant_units,
                        "observation_text": eval_res["observation_text"],
                        "rationale": rule.rationale,
                    }
                    observations.append(obs_entry)
                    advisories.append({
                        "rule_id": rule.rule_id,
                        "title": rule.title,
                        "advisory_message": eval_res["observation_text"],
                        "source_url": rule.source_url,
                    })
                    sources.append({
                        "rule_id": rule.rule_id,
                        "source_organization": rule.source_organization,
                        "source_url": rule.source_url,
                        "publication_year": rule.publication_year,
                        "jurisdiction": rule.jurisdiction,
                    })

        return HealthAssessmentResult(
            status="available",
            health_impact_score=None,
            observations=observations,
            advisories=advisories,
            missing_data_notices=missing_notices,
            warnings=warnings,
            sources=sources,
            limitations=limitations,
        )
