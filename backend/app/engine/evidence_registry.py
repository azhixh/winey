"""
Scientific and regulatory evidence registry for BQAS.

Strict requirements:
- Each rule must contain: rule ID, description, source organization, exact source URL,
  publication/revision year, applicable category, jurisdiction, relevant units/conditions,
  evidence review status, and last verification date.
- Rules cannot be activated until their source and applicability have been reviewed.
- Never invents scientific thresholds.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from app.engine.normalization import NormalizedBeverageData


@dataclass
class EvidenceRule:
    """
    Structured scientific or regulatory rule backed by an authoritative publication.
    """
    rule_id: str
    title: str
    description: str
    source_organization: str
    source_url: str
    publication_year: int
    applicable_categories: list[str]  # e.g. ["Soft drink", "Energy drink"] or ["Beer", "Wine", "Spirits"]
    jurisdiction: str                 # e.g. "International", "European Union", "United States"
    relevant_units: str               # e.g. "g/100 mL", "% ABV", "mg/serving"
    conditions: str                   # Human-readable criteria description
    evidence_review_status: str       # "reviewed", "under_review", "unreviewed"
    last_verification_date: str       # ISO 8601 date, e.g. "2026-01-15"
    rationale: str
    is_active: bool = True
    evaluator: Optional[Callable[[NormalizedBeverageData], Optional[dict[str, Any]]]] = None

    def is_applicable_to(self, beverage_type: str) -> bool:
        """Check category matching."""
        if not self.is_active:
            return False
        if self.evidence_review_status not in ("reviewed", "active"):
            return False
        clean = beverage_type.strip().lower()
        return clean in [c.strip().lower() for c in self.applicable_categories]


@dataclass
class EvidenceObservation:
    """
    Evidence-grounded finding produced from an active EvidenceRule.
    """
    rule_id: str
    title: str
    source_organization: str
    source_url: str
    publication_year: int
    jurisdiction: str
    relevant_units: str
    observation_text: str
    rationale: str


# =====================================================================
# Pre-Defined Authoritative Evidence Rules
# =====================================================================

def _eval_who_alcohol(data: NormalizedBeverageData) -> Optional[dict[str, Any]]:
    has_alcohol = (data.alcohol_percentage is not None and data.alcohol_percentage > 0.0)
    is_alc_type = data.beverage_type.value in ["Beer", "Wine", "Spirits"]
    if has_alcohol or is_alc_type:
        return {
            "observation_text": (
                "According to the World Health Organization (2023), there is no evidence of a threshold "
                "at which the carcinogenic and health risks of alcohol consumption are absent; "
                "no level of alcohol consumption is risk-free for health."
            )
        }
    return None


def _eval_who_sugar(data: NormalizedBeverageData) -> Optional[dict[str, Any]]:
    # Only evaluate if sugar data is present
    if data.sugar_g is not None or data.sugar_concentration_g_per_100ml is not None:
        conc = data.sugar_concentration_g_per_100ml
        serving = data.sugar_g
        details = []
        if serving is not None:
            details.append(f"{serving} g/serving")
        if conc is not None:
            details.append(f"{conc} g/100 mL")
        sugar_str = f" ({', '.join(details)})" if details else ""

        return {
            "observation_text": (
                f"Reported sugar content{sugar_str} is evaluated in light of the WHO Guideline (2015), "
                "which recommends reducing free sugars intake throughout the lifecourse due to evidence "
                "linking intake to dental caries and unhealthy weight gain."
            )
        }
    return None


def _eval_efsa_caffeine(data: NormalizedBeverageData) -> Optional[dict[str, Any]]:
    if data.beverage_type.value == "Energy drink":
        if data.caffeine_mg is not None:
            return {
                "observation_text": (
                    f"Reported caffeine content ({data.caffeine_mg} mg/serving) evaluated under the EFSA Scientific "
                    "Opinion on Caffeine Safety (2015). EFSA notes single doses up to 200 mg and daily intakes up to 400 mg "
                    "do not raise safety concerns for healthy adults, but advises caution regarding rapid consumption and "
                    "combination with alcohol or intense physical activity."
                )
            }
        else:
            return {
                "observation_text": (
                    "Energy drink formulation does not report quantitative caffeine content. "
                    "EFSA (2015) guidance highlights that caffeine disclosure is essential for evaluating "
                    "single-dose and daily intake boundaries."
                )
            }
    return None


WHO_ALCOHOL_RULE = EvidenceRule(
    rule_id="WHO_ALCOHOL_RISK_2023",
    title="WHO Statement on Alcohol Consumption and Health Risks",
    description="Authoritative WHO statement establishing the absence of a health risk-free threshold for alcohol consumption.",
    source_organization="World Health Organization (WHO) Regional Office for Europe",
    source_url="https://www.who.int/europe/news/item/04-01-2023-no-level-of-alcohol-consumption-is-safe-for-our-health",
    publication_year=2023,
    applicable_categories=["Beer", "Wine", "Spirits"],
    jurisdiction="International",
    relevant_units="% ABV / g ethanol",
    conditions="Applicable to any alcoholic beverage category or any beverage reporting alcohol_percentage > 0.",
    evidence_review_status="reviewed",
    last_verification_date="2026-01-15",
    rationale="Alcohol is a Group 1 human carcinogen causally linked to breast, liver, and colorectal cancers, with no identified safe consumption cutoff.",
    is_active=True,
    evaluator=_eval_who_alcohol,
)

WHO_SUGAR_RULE = EvidenceRule(
    rule_id="WHO_SUGARS_GUIDELINE_2015",
    title="WHO Guideline on Sugars Intake for Adults and Children",
    description="Evidence-based guidance on the health impacts of free sugars intake.",
    source_organization="World Health Organization (WHO)",
    source_url="https://www.who.int/publications/i/item/9789241549028",
    publication_year=2015,
    applicable_categories=["Soft drink", "Energy drink"],
    jurisdiction="International",
    relevant_units="g sugar/serving, g sugar/100 mL",
    conditions="Applicable to non-alcoholic beverages with reported sugar content.",
    evidence_review_status="reviewed",
    last_verification_date="2026-01-15",
    rationale="Systematic review of evidence linking free sugars intake to excess adiposity, non-communicable diseases, and dental caries.",
    is_active=True,
    evaluator=_eval_who_sugar,
)

EFSA_CAFFEINE_RULE = EvidenceRule(
    rule_id="EFSA_CAFFEINE_SAFETY_2015",
    title="EFSA Scientific Opinion on the Safety of Caffeine",
    description="Risk assessment on single-dose and habitual daily intakes of caffeine from beverages.",
    source_organization="European Food Safety Authority (EFSA)",
    source_url="https://www.efsa.europa.eu/en/efsajournal/pub/4102",
    publication_year=2015,
    applicable_categories=["Energy drink"],
    jurisdiction="European Union",
    relevant_units="mg caffeine",
    conditions="Applicable to energy drinks and formulated caffeinated beverages.",
    evidence_review_status="reviewed",
    last_verification_date="2026-01-15",
    rationale="Comprehensive scientific evaluation of acute and chronic cardiovascular and central nervous system effects of caffeine.",
    is_active=True,
    evaluator=_eval_efsa_caffeine,
)


class EvidenceRegistry:
    """
    Registry for managing reviewed scientific and regulatory evidence rules.
    """

    def __init__(self, initial_rules: Optional[list[EvidenceRule]] = None):
        self._rules: dict[str, EvidenceRule] = {}
        defaults = initial_rules if initial_rules is not None else [
            WHO_ALCOHOL_RULE,
            WHO_SUGAR_RULE,
            EFSA_CAFFEINE_RULE,
        ]
        for rule in defaults:
            self.register_rule(rule)

    def register_rule(self, rule: EvidenceRule) -> None:
        """
        Register a scientific or regulatory rule.
        Enforces that unreviewed rules cannot be marked active.
        """
        if rule.evidence_review_status not in ("reviewed", "active"):
            # Cannot activate unreviewed rules
            rule.is_active = False

        self._rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> Optional[EvidenceRule]:
        return self._rules.get(rule_id)

    def get_active_rules(self, beverage_type: Optional[str] = None) -> list[EvidenceRule]:
        """Return active, reviewed rules, optionally filtered by beverage category."""
        active = [r for r in self._rules.values() if r.is_active and r.evidence_review_status in ("reviewed", "active")]
        if beverage_type is None:
            return active
        return [r for r in active if r.is_applicable_to(beverage_type)]

    def count(self) -> int:
        return len(self._rules)
