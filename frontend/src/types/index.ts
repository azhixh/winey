/**
 * BQAS TypeScript Core Type Definitions
 * Exact mirrors of PRD Section 12 contracts, Step 6 Backend schemas,
 * and frontend application states.
 */

export type BeverageCategory =
  | 'Soft drink'
  | 'Beer'
  | 'Wine'
  | 'Spirits'
  | 'Energy drink';

export interface UserProfile {
  age_group: 'adult' | 'under_18';
  weight_kg: number;
  is_pregnant_or_breastfeeding: boolean;
  has_diabetes: boolean;
  has_heart_condition: boolean;
  regulator_region: string;
  standard_drink_definition_g: number;
}

export interface IngredientSubscore {
  ingredient_key: string;
  ingredient_name: string;
  amount_per_serving: number;
  amount_per_100ml?: number | null;
  unit: string;
  guideline_limit: number;
  guideline_ratio: number;
  band: 'Favourable' | 'Moderate' | 'Caution' | 'High';
  subscore: number;
  daily_limit?: number | null;
  daily_share?: number | null;
  is_critical_breach: boolean;
  source_organization: string;
  source_url: string;
  publication_year?: number | null;
  rationale: string;
}

export interface IngredientBenchmark {
  ingredient_key: string;
  amount_evaluated: number;
  unit: string;
  status:
    | 'lower_than_typical'
    | 'typical'
    | 'higher_than_typical'
    | 'very_high'
    | 'limited_benchmark_data';
  credit?: number | null;
  percentile_band?: string | null;
  sample_size: number;
  is_sufficient: boolean;
  risk_direction: string;
}

export interface CriticalOverrideInfo {
  is_critical: boolean;
  capped_score?: number | null;
  uncapped_score?: number | null;
  banner_color?: string | null;
  critical_reasons: string[];
}

export interface WineModelResult {
  is_available: boolean;
  predicted_quality?: number | null;
  predicted_rating?: number | null;
  reason_if_unavailable?: string | null;
  test_mae?: number | null;
  model_limitations?: string | null;
  disclaimer?: string | null;
}

export interface ScoringEngineResult {
  beverage_type: BeverageCategory;
  serving_size_ml: number;
  product_name?: string | null;

  // Strictly separated scores
  health_impact_score?: number | null;
  uncapped_health_impact_score?: number | null;
  composition_score?: number | null;

  guideline_evaluations: IngredientSubscore[];
  benchmark_evaluations: IngredientBenchmark[];

  alcohol_grams?: number | null;
  standard_drinks?: number | null;
  alcohol_advisory?: string | null;

  critical_override: CriticalOverrideInfo;
  confidence_level: 'High' | 'Medium' | 'Low';
  confidence_percentage: number;
  is_partial_analysis: boolean;

  higher_than_typical: string[];
  lower_than_typical: string[];
  missing_fields: string[];
  warnings: string[];
  disclaimer: string;

  rules_version: string;
  dataset_version: string;
  wine_model?: WineModelResult | null;
}

export interface ScoringEvaluationRequest {
  beverage_type: BeverageCategory;
  serving_size_ml: number;
  product_name?: string;
  wine_color?: 'red' | 'white';
  inputs: Record<string, any>;
  profile?: UserProfile;
}

export interface HistoryRecord {
  id: string;
  timestamp: string;
  product_name: string;
  beverage_type: BeverageCategory;
  serving_size_ml: number;
  health_impact_score?: number | null;
  composition_score?: number | null;
  confidence_level: string;
  is_critical: boolean;
  rules_version: string;
  dataset_version: string;
  result: ScoringEngineResult;
}

export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  unitSystem: 'metric' | 'imperial';
  defaultRegion: string;
  standardDrinkDef: number;
  highContrast: boolean;
}

export interface BenchmarkDistribution {
  unit: string;
  sample_size: number;
  source: string;
  description: string;
  percentiles: {
    p5: number;
    p25: number;
    p50: number;
    p75: number;
    p95: number;
  };
}

export interface CategoryBenchmarks {
  [metricName: string]: BenchmarkDistribution;
}

export interface ReferenceRangesData {
  dataset_version: string;
  last_updated: string;
  categories: {
    [categoryKey: string]: CategoryBenchmarks;
  };
}

export interface GuidelineRule {
  name: string;
  target_group: string;
  risk_direction: 'high_is_bad' | 'low_is_bad' | 'both_directions' | 'info_only';
  weight: number;
  ideal_target_g_day?: number;
  cap_limit_g_day?: number;
  single_dose_limit_adult_mg?: number;
  daily_limit_adult_mg?: number;
  daily_limit_under_18_mg_per_kg?: number;
  daily_limit_pregnant_mg?: number;
  adi_mg_per_kg_body_weight?: number;
  max_limit_g_per_l_pure_alcohol?: number;
  source_organization: string;
  source_url: string;
  publication_year?: number;
  rationale: string;
  verification_status: string;
}

export interface RulesData {
  rules_version: string;
  last_updated: string;
  general_constants: {
    ethanol_density_g_ml: number;
    standard_drink_g_who: number;
    minimum_benchmark_samples: number;
  };
  guideline_rules: {
    [key: string]: GuidelineRule;
  };
  critical_override: {
    capped_health_impact_score: number;
    banner_color: string;
  };
  confidence_levels: {
    high_threshold: number;
    medium_threshold: number;
  };
  composition_credits: {
    typical: number;
    lower_than_typical: { high_is_bad: number; other: number };
    higher_than_typical: { high_is_bad: number; other: number };
    very_high: { high_is_bad: number; other: number };
  };
}
