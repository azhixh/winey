"""
Unit tests for app.engine.evidence_registry.

Verifies:
- Required attributes on all scientific and regulatory rules (rule ID, description,
  source organization, exact URL, publication year, category, jurisdiction, units,
  review status, verification date, rationale).
- Unreviewed rules cannot be activated.
- Under-review rules cannot be activated.
- Active rules can be queried by category.
- Mismatched categories are rejected.
- Evaluators execute without inventing scientific thresholds.
- Default authoritative rules (WHO Alcohol 2023, WHO Sugars 2015, EFSA Caffeine 2015).
"""

import pytest
from app.engine.evidence_registry import (
    EvidenceRule,
    EvidenceRegistry,
    WHO_ALCOHOL_RULE,
    WHO_SUGAR_RULE,
    EFSA_CAFFEINE_RULE,
)
from app.engine.normalization import normalize_beverage_input
from app.schemas import BeverageType


def test_who_alcohol_rule_provenance_and_fields():
    """Verify WHO alcohol rule complies with all required registry fields."""
    rule = WHO_ALCOHOL_RULE
    assert rule.rule_id == "WHO_ALCOHOL_RISK_2023"
    assert rule.publication_year == 2023
    assert "World Health Organization" in rule.source_organization
    assert rule.source_url == "https://www.who.int/europe/news/item/04-01-2023-no-level-of-alcohol-consumption-is-safe-for-our-health"
    assert rule.jurisdiction == "International"
    assert rule.evidence_review_status == "reviewed"
    assert rule.last_verification_date == "2026-01-15"
    assert rule.is_active is True
    assert "Beer" in rule.applicable_categories
    assert "Wine" in rule.applicable_categories
    assert "Spirits" in rule.applicable_categories
    assert "% ABV" in rule.relevant_units
    assert "no identified safe consumption cutoff" in rule.rationale.lower()


def test_who_sugar_rule_provenance_and_fields():
    """Verify WHO sugar guideline complies with all required registry fields."""
    rule = WHO_SUGAR_RULE
    assert rule.rule_id == "WHO_SUGARS_GUIDELINE_2015"
    assert rule.publication_year == 2015
    assert "World Health Organization" in rule.source_organization
    assert rule.source_url == "https://www.who.int/publications/i/item/9789241549028"
    assert rule.jurisdiction == "International"
    assert rule.evidence_review_status == "reviewed"
    assert rule.last_verification_date == "2026-01-15"
    assert rule.is_active is True
    assert "Soft drink" in rule.applicable_categories
    assert "Energy drink" in rule.applicable_categories
    assert "g sugar" in rule.relevant_units


def test_efsa_caffeine_rule_provenance_and_fields():
    """Verify EFSA caffeine safety opinion complies with all required registry fields."""
    rule = EFSA_CAFFEINE_RULE
    assert rule.rule_id == "EFSA_CAFFEINE_SAFETY_2015"
    assert rule.publication_year == 2015
    assert "European Food Safety Authority" in rule.source_organization
    assert rule.source_url == "https://www.efsa.europa.eu/en/efsajournal/pub/4102"
    assert rule.jurisdiction == "European Union"
    assert rule.evidence_review_status == "reviewed"
    assert rule.last_verification_date == "2026-01-15"
    assert rule.is_active is True
    assert "Energy drink" in rule.applicable_categories
    assert "mg caffeine" in rule.relevant_units


def test_unreviewed_rule_cannot_be_activated():
    """Rules with evidence_review_status='unreviewed' must never be active."""
    unreviewed = EvidenceRule(
        rule_id="UNREVIEWED_HYPOTHESIS_001",
        title="Unverified Botanical Extract Effect",
        description="Hypothetical claim from preprint paper.",
        source_organization="Self-Published Lab",
        source_url="https://example.com/preprint",
        publication_year=2025,
        applicable_categories=["Soft drink"],
        jurisdiction="Global",
        relevant_units="mg/L",
        conditions="Preliminary finding",
        evidence_review_status="unreviewed",
        last_verification_date="2026-01-01",
        rationale="Unverified hypothesis.",
        is_active=True,  # Attempting to declare active
    )
    registry = EvidenceRegistry(initial_rules=[])
    registry.register_rule(unreviewed)

    registered = registry.get_rule("UNREVIEWED_HYPOTHESIS_001")
    assert registered is not None
    assert registered.is_active is False
    assert registered.is_applicable_to("Soft drink") is False

    # Should not appear in active rules
    active_rules = registry.get_active_rules("Soft drink")
    assert len(active_rules) == 0


def test_under_review_rule_cannot_be_activated():
    """Rules with evidence_review_status='under_review' must not be active."""
    under_review = EvidenceRule(
        rule_id="UNDER_REVIEW_002",
        title="Pending Regulatory Decision",
        description="Draft agency statement pending public consultation.",
        source_organization="Food Agency",
        source_url="https://example.com/draft",
        publication_year=2026,
        applicable_categories=["Energy drink"],
        jurisdiction="Regional",
        relevant_units="mg/100 mL",
        conditions="Consultation phase",
        evidence_review_status="under_review",
        last_verification_date="2026-02-01",
        rationale="Pending completion of scientific review.",
        is_active=True,
    )
    registry = EvidenceRegistry(initial_rules=[])
    registry.register_rule(under_review)

    registered = registry.get_rule("UNDER_REVIEW_002")
    assert registered.is_active is False
    assert len(registry.get_active_rules("Energy drink")) == 0


def test_reviewed_rule_can_be_activated():
    """Rules with evidence_review_status='reviewed' remain active."""
    reviewed = EvidenceRule(
        rule_id="REVIEWED_RULE_003",
        title="Validated Rule",
        description="Fully vetted guideline.",
        source_organization="Public Health Body",
        source_url="https://example.gov/guideline",
        publication_year=2022,
        applicable_categories=["Soft drink"],
        jurisdiction="National",
        relevant_units="g/100 mL",
        conditions="Standard peer-reviewed criteria",
        evidence_review_status="reviewed",
        last_verification_date="2026-01-10",
        rationale="Supported by systematic review.",
        is_active=True,
    )
    registry = EvidenceRegistry(initial_rules=[])
    registry.register_rule(reviewed)

    registered = registry.get_rule("REVIEWED_RULE_003")
    assert registered.is_active is True
    assert registered.is_applicable_to("Soft drink") is True
    assert registered.is_applicable_to("soft drink") is True
    assert len(registry.get_active_rules("Soft drink")) == 1


def test_mismatched_beverage_categories_filtered_out():
    """Rules must only match their designated beverage categories."""
    registry = EvidenceRegistry()  # Contains default 3 rules

    soft_rules = registry.get_active_rules("Soft drink")
    assert any(r.rule_id == "WHO_SUGARS_GUIDELINE_2015" for r in soft_rules)
    assert not any(r.rule_id == "WHO_ALCOHOL_RISK_2023" for r in soft_rules)
    assert not any(r.rule_id == "EFSA_CAFFEINE_SAFETY_2015" for r in soft_rules)

    beer_rules = registry.get_active_rules("Beer")
    assert any(r.rule_id == "WHO_ALCOHOL_RISK_2023" for r in beer_rules)
    assert not any(r.rule_id == "WHO_SUGARS_GUIDELINE_2015" for r in beer_rules)
    assert not any(r.rule_id == "EFSA_CAFFEINE_SAFETY_2015" for r in beer_rules)

    energy_rules = registry.get_active_rules("Energy drink")
    assert any(r.rule_id == "EFSA_CAFFEINE_SAFETY_2015" for r in energy_rules)
    assert any(r.rule_id == "WHO_SUGARS_GUIDELINE_2015" for r in energy_rules)
    assert not any(r.rule_id == "WHO_ALCOHOL_RISK_2023" for r in energy_rules)

    # Unknown category returns nothing
    unknown_rules = registry.get_active_rules("Kombucha")
    assert len(unknown_rules) == 0


def test_who_alcohol_evaluator_triggers_on_alcohol_presence():
    """WHO alcohol evaluator triggers whenever alcohol is present or category is alcoholic."""
    norm_beer = normalize_beverage_input(
        beverage_type=BeverageType.BEER,
        serving_size=330.0,
        alcohol_percentage=4.5,
    )
    result = WHO_ALCOHOL_RULE.evaluator(norm_beer)
    assert result is not None
    assert "no level of alcohol consumption is risk-free" in result["observation_text"]

    # Non-alcoholic drink with zero alcohol does not trigger
    norm_soft = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=330.0,
        sugar=25.0,
        alcohol_percentage=0.0,
    )
    # The rule is not applicable to soft drink in registry, but evaluator directly:
    soft_eval = WHO_ALCOHOL_RULE.evaluator(norm_soft)
    assert soft_eval is None


def test_who_sugar_evaluator_triggers_when_sugar_is_reported():
    """WHO sugar evaluator produces evidence observation when sugar metrics are present."""
    norm_soft = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=250.0,
        sugar=26.0,
    )
    result = WHO_SUGAR_RULE.evaluator(norm_soft)
    assert result is not None
    assert "26.0 g/serving" in result["observation_text"]
    assert "WHO Guideline (2015)" in result["observation_text"]

    # When sugar is omitted
    norm_empty = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=250.0,
    )
    assert WHO_SUGAR_RULE.evaluator(norm_empty) is None


def test_efsa_caffeine_evaluator_handles_reported_and_unreported_caffeine():
    """EFSA evaluator handles both reported caffeine and missing caffeine disclosures."""
    # Reported caffeine
    norm_energy = normalize_beverage_input(
        beverage_type=BeverageType.ENERGY_DRINK,
        serving_size=250.0,
        caffeine=80.0,
    )
    result = EFSA_CAFFEINE_RULE.evaluator(norm_energy)
    assert result is not None
    assert "80.0 mg/serving" in result["observation_text"]
    assert "EFSA Scientific Opinion on Caffeine Safety (2015)" in result["observation_text"]

    # Unreported caffeine
    norm_energy_no_caf = normalize_beverage_input(
        beverage_type=BeverageType.ENERGY_DRINK,
        serving_size=250.0,
    )
    result_no_caf = EFSA_CAFFEINE_RULE.evaluator(norm_energy_no_caf)
    assert result_no_caf is not None
    assert "does not report quantitative caffeine content" in result_no_caf["observation_text"]
