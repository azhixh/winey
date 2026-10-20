import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Coffee,
  Beer,
  Zap,
  Wine,
  Flame,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  BookOpen,
  Info,
} from 'lucide-react';
import { getScoringBenchmarks } from '../services/api';
import type { ReferenceRangesData, BeverageCategory } from '../types';

interface CategoryConfig {
  id: string;
  categoryKey: string;
  name: string;
  beverageCategory: BeverageCategory;
  desc: string;
  icon: React.ElementType;
  color: string;
  typicalIngredients: { name: string; unit: string; purpose: string }[];
  healthConsiderations: { title: string; desc: string; source: string; year: number }[];
  sources: { title: string; org: string; year: number; url: string }[];
}

const CATEGORY_MAP: Record<string, CategoryConfig> = {
  'soft-drinks': {
    id: 'soft-drinks',
    categoryKey: 'Soft drink',
    name: 'Soft Drinks',
    beverageCategory: 'Soft drink',
    desc: 'Carbonated non-alcoholic sweetened waters, colas, flavored sparkling beverages, and fruit sodas.',
    icon: Coffee,
    color: '#3B82F6',
    typicalIngredients: [
      { name: 'Free Sugars (Sucrose / HFCS)', unit: 'g/serving', purpose: 'Sweetness and body' },
      { name: 'Energy (Calories)', unit: 'kcal/serving', purpose: 'Caloric load' },
      { name: 'Caffeine', unit: 'mg/serving', purpose: 'Stimulant and flavor enhancer' },
      { name: 'Sodium', unit: 'mg/serving', purpose: 'Electrolyte balance' },
      { name: 'Sodium Benzoate (E211)', unit: 'mg/L', purpose: 'Antimicrobial preservation' },
      { name: 'Phosphoric Acid', unit: 'mg/L', purpose: 'Tartness and cola flavor' },
      { name: 'pH Level', unit: 'pH', purpose: 'Acidity / dental erosion factor' },
    ],
    healthConsiderations: [
      {
        title: 'Free Sugars & Metabolic Impact',
        desc: 'Frequent intake of sugar-sweetened beverages is associated with elevated risk of type-2 diabetes, cardiovascular disease, and tooth decay.',
        source: 'WHO Guideline: Sugars intake for adults and children',
        year: 2015,
      },
      {
        title: 'Preservative Benzoate Exposure',
        desc: 'Sodium benzoate is converted to benzoic acid in the stomach. JECFA established an Acceptable Daily Intake (ADI) of 5 mg/kg body weight.',
        source: 'FAO/WHO JECFA Evaluation of Benzoates',
        year: 2021,
      },
      {
        title: 'Dental Enamel Demineralization',
        desc: 'Beverages with pH < 4.0 or high phosphoric acid concentrations can cause progressive dental enamel erosion.',
        source: 'EFSA Panel on Dietetic Products, Nutrition and Allergies',
        year: 2011,
      },
    ],
    sources: [
      { title: 'Guideline: Sugars intake for adults and children', org: 'WHO', year: 2015, url: 'https://www.who.int/publications/i/item/9789241549028' },
      { title: 'Scientific Opinion on the safety of caffeine', org: 'EFSA', year: 2015, url: 'https://doi.org/10.2903/j.efsa.2015.4102' },
      { title: 'Toxicological Evaluation of Certain Food Additives', org: 'JECFA/WHO', year: 2021, url: 'https://apps.who.int/iris/handle/10665/341908' },
    ],
  },
  beer: {
    id: 'beer',
    categoryKey: 'Beer',
    name: 'Beer & Ales',
    beverageCategory: 'Beer',
    desc: 'Fermented malt beverages including lagers, ales, stouts, pilsners, and craft beers.',
    icon: Beer,
    color: '#F59E0B',
    typicalIngredients: [
      { name: 'Alcohol (% ABV)', unit: '% vol', purpose: 'Fermented ethanol strength' },
      { name: 'Energy (Calories)', unit: 'kcal/serving', purpose: 'Ethanol + carbohydrate energy' },
      { name: 'Carbohydrates', unit: 'g/serving', purpose: 'Residual unfermented dextrins' },
      { name: 'Sulphites as SO2', unit: 'mg/L', purpose: 'Antioxidant & freshness preservation' },
      { name: 'Bitterness (IBU)', unit: 'IBU', purpose: 'Iso-alpha-acids from hops' },
    ],
    healthConsiderations: [
      {
        title: 'No Safe Level of Alcohol Consumption',
        desc: 'The World Health Organization explicitly affirms that no level of alcohol consumption is completely safe for human health. Ethanol is a Group 1 carcinogen.',
        source: 'WHO Alcohol Policy Fact Sheet',
        year: 2023,
      },
      {
        title: 'Sulphite Sensitivity & Bronchospasm',
        desc: 'Sulphites may provoke severe allergic or asthmatic reactions in sensitive individuals. EFSA established an ADI of 0.7 mg/kg body weight.',
        source: 'EFSA Scientific Opinion on Sulphites',
        year: 2016,
      },
      {
        title: 'Caloric & Glycemic Load',
        desc: 'Residual maltose and carbohydrates coupled with ethanol contribute substantially to total daily dietary energy.',
        source: 'USDA FoodData Central / Dietary Guidelines',
        year: 2020,
      },
    ],
    sources: [
      { title: 'Alcohol and Health Guidance Report', org: 'WHO', year: 2023, url: 'https://www.who.int/news-room/fact-sheets/detail/alcohol' },
      { title: 'Re-evaluation of sulfur dioxide (E 220) and sulfites (E 221-228)', org: 'EFSA', year: 2016, url: 'https://doi.org/10.2903/j.efsa.2016.4438' },
    ],
  },
  'energy-drinks': {
    id: 'energy-drinks',
    categoryKey: 'Energy drink',
    name: 'Energy Drinks',
    beverageCategory: 'Energy drink',
    desc: 'Functional stimulant beverages formulated with caffeine, taurine, sugars or sweeteners, and B-vitamins.',
    icon: Zap,
    color: '#10B981',
    typicalIngredients: [
      { name: 'Caffeine', unit: 'mg/serving', purpose: 'Central nervous system stimulant' },
      { name: 'Free Sugars', unit: 'g/serving', purpose: 'Rapid energy substrate' },
      { name: 'Taurine', unit: 'mg/serving', purpose: 'Neuromodulatory amino acid' },
      { name: 'Sodium', unit: 'mg/serving', purpose: 'Mineral balance' },
      { name: 'B-Complex Vitamins', unit: 'mg/serving', purpose: 'Metabolic co-factors' },
      { name: 'Guarana / Herbal Extracts', unit: 'mg/serving', purpose: 'Secondary botanical caffeine sources' },
    ],
    healthConsiderations: [
      {
        title: 'Acute Caffeine Single-Dose Limit (200 mg)',
        desc: 'EFSA clinical reviews establish that single caffeine doses up to 200 mg do not raise safety concerns in healthy adults. Doses exceeding 200 mg or 3 mg/kg in minors provoke autonomic arousal.',
        source: 'EFSA Scientific Opinion on the safety of caffeine',
        year: 2015,
      },
      {
        title: 'Dual Stimulant & Sugar Shock',
        desc: 'Combining high acute caffeine with large doses of rapid sugars can cause heightened cardiovascular stress, tachycardia, and blood pressure spikes.',
        source: 'American Heart Association Beverage Analysis',
        year: 2019,
      },
      {
        title: 'Taurine Safety Threshold',
        desc: 'EFSA panel evaluations determined that taurine intakes up to 1,000 mg/serving are not associated with adverse toxicological outcomes.',
        source: 'EFSA Panel on Food Additives and Nutrient Sources',
        year: 2009,
      },
    ],
    sources: [
      { title: 'Scientific Opinion on the safety of caffeine', org: 'EFSA', year: 2015, url: 'https://doi.org/10.2903/j.efsa.2015.4102' },
      { title: 'The use of taurine in energy drinks', org: 'EFSA Journal', year: 2009, url: 'https://doi.org/10.2903/j.efsa.2009.935' },
    ],
  },
  wine: {
    id: 'wine',
    categoryKey: 'Wine_red',
    name: 'Wine (Red & White)',
    beverageCategory: 'Wine',
    desc: 'Naturally fermented grape wines classified by red or white varietal, assessed for residual sugars, sulfur dioxide, and sensory quality.',
    icon: Wine,
    color: '#8B5CF6',
    typicalIngredients: [
      { name: 'Alcohol (% vol)', unit: '% vol', purpose: 'Natural grape ethanol' },
      { name: 'Residual Sugar', unit: 'g/L', purpose: 'Unfermented fructose & glucose' },
      { name: 'Total Sulfur Dioxide (SO2)', unit: 'mg/L', purpose: 'Antimicrobial and antioxidant protection' },
      { name: 'pH Level', unit: 'pH', purpose: 'Acidic balance and microbial stability' },
      { name: 'Fixed & Volatile Acidity', unit: 'g/L', purpose: 'Tartaric and acetic acid components' },
      { name: 'Chlorides & Sulphates', unit: 'g/L', purpose: 'Mineral salinity and preservation' },
    ],
    healthConsiderations: [
      {
        title: 'Carcinogenic Risk of Ethanol',
        desc: 'Regardless of wine type or antioxidant polyphenol claims, alcohol is metabolized into acetaldehyde and is classified by IARC as a Group 1 human carcinogen.',
        source: 'WHO Regional Office for Europe / IARC Monograph',
        year: 2023,
      },
      {
        title: 'Sulfites (SO2) Asthmatic Sensitivity',
        desc: 'Free and bound sulfur dioxide in wines can provoke acute bronchospasms in individuals with sulfite-sensitive asthma.',
        source: 'EFSA Journal / FDA Food Labeling Rules',
        year: 2016,
      },
      {
        title: 'Sensory Quality vs. Health Scoring',
        desc: 'Expert sensory quality prediction (UCI Vinho Verde dataset) reflects organoleptic taste properties and is NOT a measure of healthiness.',
        source: 'Cortez et al., Modeling wine preferences by data mining',
        year: 2009,
      },
    ],
    sources: [
      { title: 'No level of alcohol consumption is safe for our health', org: 'WHO Europe', year: 2023, url: 'https://www.who.int/europe/news/item/04-01-2023-no-level-of-alcohol-consumption-is-safe-for-our-health' },
      { title: 'Modeling wine preferences by data mining from physicochemical properties', org: 'Decision Support Systems (UCI)', year: 2009, url: 'https://archive.ics.uci.edu/dataset/186/wine+quality' },
    ],
  },
  alcohol: {
    id: 'alcohol',
    categoryKey: 'Alcohol',
    name: 'Alcohol / Spirits',
    beverageCategory: 'Spirits',
    desc: 'Distilled spirits including whiskey, gin, rum, vodka, tequila, and brandies with high volumetric alcohol concentration.',
    icon: Flame,
    color: '#EF4444',
    typicalIngredients: [
      { name: 'Alcohol By Volume (ABV)', unit: '% ABV', purpose: 'Distilled ethanol strength (typically 35% - 50%)' },
      { name: 'Methanol', unit: 'g/L pure alcohol', purpose: 'Naturally occurring toxic congener (strict max limit 10 g/L)' },
      { name: 'Added Sugars', unit: 'g/L', purpose: 'Sweetener load in liqueurs and flavored spirits' },
      { name: 'Congeners', unit: 'mg/L', purpose: 'Trace fusel oils, esters, and aldehydes from distillation' },
    ],
    healthConsiderations: [
      {
        title: 'Methanol Toxicity & Critical Health Breach',
        desc: 'Methanol is metabolized to formaldehyde and formic acid, causing metabolic acidosis and irreversible optic nerve damage. Exceeding 10.0 g/L pure alcohol immediately triggers a Critical Health Override, capping the score at 40.',
        source: 'EU Regulation 2019/787 on Spirit Drinks',
        year: 2019,
      },
      {
        title: 'High-Strength Ethanol Impact',
        desc: 'Distilled spirits provide rapid blood alcohol concentration (BAC) elevation. WHO guidelines emphasize standard drink equivalents (10g pure ethanol per standard drink).',
        source: 'WHO Global Strategy to Reduce the Harmful Use of Alcohol',
        year: 2022,
      },
      {
        title: 'Absolute Avoidance in Pregnancy & Minors',
        desc: 'Spirits consumption during pregnancy carries high risk of Fetal Alcohol Spectrum Disorders (FASD). Strict contraindication applies.',
        source: 'WHO Guidelines on Alcohol and Pregnancy',
        year: 2020,
      },
    ],
    sources: [
      { title: 'Regulation (EU) 2019/787 on the definition and labelling of spirit drinks', org: 'European Parliament', year: 2019, url: 'https://eur-lex.europa.eu/eli/reg/2019/787/oj' },
      { title: 'Global status report on alcohol and health', org: 'WHO', year: 2018, url: 'https://www.who.int/publications/i/item/9789241565639' },
    ],
  },
};

export const DrinksPage: React.FC = () => {
  const { category: routeCategory } = useParams<{ category: string }>();
  const navigate = useNavigate();

  const [benchmarksData, setBenchmarksData] = useState<ReferenceRangesData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const selectedCategory = routeCategory && CATEGORY_MAP[routeCategory] ? CATEGORY_MAP[routeCategory] : CATEGORY_MAP['soft-drinks'];
  const IconComponent = selectedCategory.icon;

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    getScoringBenchmarks()
      .then((data) => {
        if (isMounted) {
          setBenchmarksData(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error('Failed to load benchmarks:', err);
          setError('Failed to load benchmark reference ranges from backend server.');
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [routeCategory]);

  // Extract category benchmarks from the returned dataset
  const categoryBenchmarks =
    benchmarksData?.categories?.[selectedCategory.categoryKey] ||
    (selectedCategory.id === 'wine' ? benchmarksData?.categories?.['Wine_red'] : null);

  const handleAnalyzeClick = () => {
    navigate(`/lab?category=${encodeURIComponent(selectedCategory.beverageCategory)}`);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2xl)' }}>
      {/* Category Navigation Pills */}
      <div
        style={{
          display: 'flex',
          gap: 'var(--space-xs)',
          overflowX: 'auto',
          paddingBottom: 'var(--space-xs)',
        }}
      >
        {Object.values(CATEGORY_MAP).map((cat) => {
          const isCurrent = cat.id === selectedCategory.id;
          const CatIcon = cat.icon;
          return (
            <Link
              key={cat.id}
              to={`/drinks/${cat.id}`}
              className={`btn ${isCurrent ? 'btn-primary' : 'btn-secondary'}`}
              style={{
                borderRadius: 'var(--radius-pill)',
                padding: '8px 16px',
                fontSize: '0.875rem',
              }}
            >
              <CatIcon size={16} />
              <span>{cat.name}</span>
            </Link>
          );
        })}
      </div>

      {/* Header Banner */}
      <section
        className="glass-panel"
        style={{
          padding: 'var(--space-2xl) var(--space-xl)',
          borderRadius: 'var(--radius-xl)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-md)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--color-surface-dim)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: selectedCategory.color,
            }}
          >
            <IconComponent size={32} />
          </div>
          <div>
            <h1>{selectedCategory.name}</h1>
            <p style={{ fontSize: '1.125rem' }}>{selectedCategory.desc}</p>
          </div>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-md)', marginTop: 'var(--space-sm)' }}>
          <button
            onClick={handleAnalyzeClick}
            className="btn btn-primary"
            style={{ padding: '0.75rem 1.5rem', fontSize: '0.9375rem' }}
          >
            <Sparkles size={18} />
            <span>Analyze This Drink</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </section>

      {/* Typical Ingredients Table */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <h2 style={{ marginBottom: 'var(--space-md)' }}>Typical Ingredients & Evaluated Metrics</h2>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--color-border)', color: 'var(--color-text-subtle)' }}>
                <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>Ingredient / Metric</th>
                <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>Canonical Unit</th>
                <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>Evaluation Purpose</th>
              </tr>
            </thead>
            <tbody>
              {selectedCategory.typicalIngredients.map((ing, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: '1px solid var(--color-border)',
                    backgroundColor: idx % 2 === 0 ? 'transparent' : 'var(--color-surface-container)',
                  }}
                >
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>{ing.name}</td>
                  <td style={{ padding: '12px 16px', color: 'var(--color-text-muted)' }}>
                    <code>{ing.unit}</code>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                    {ing.purpose}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Available Benchmark Ranges */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)' }}>
          <div>
            <h2>Empirical Category Benchmark Ranges</h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)' }}>
              Percentiles (P25, P50 Median, P75, P95) computed from verified public records with sample threshold n ≥ 100.
            </p>
          </div>
          {benchmarksData && (
            <span className="badge badge-neutral">Dataset v{benchmarksData.dataset_version}</span>
          )}
        </div>

        {loading ? (
          <div style={{ padding: 'var(--space-xl)', textAlign: 'center' }}>
            <p>Loading benchmark data from backend repository...</p>
          </div>
        ) : error ? (
          <div style={{ padding: 'var(--space-lg)', backgroundColor: 'var(--color-caution-bg)', borderRadius: 'var(--radius-md)', color: 'var(--color-caution-text)' }}>
            <AlertTriangle size={20} style={{ marginBottom: '8px' }} />
            <p>{error}</p>
          </div>
        ) : !categoryBenchmarks || Object.keys(categoryBenchmarks).length === 0 ? (
          <div style={{ padding: 'var(--space-xl)', textAlign: 'center' }}>
            <Info size={32} color="var(--color-text-subtle)" style={{ margin: '0 auto var(--space-xs)' }} />
            <p style={{ fontWeight: 600 }}>Benchmark data unavailable</p>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
              No empirical benchmark distributions meet the minimum reliability sample count (n ≥ 100) for this category yet.
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--color-border)', color: 'var(--color-text-subtle)' }}>
                  <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>Metric</th>
                  <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>Unit</th>
                  <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>Sample Size (n)</th>
                  <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>P25</th>
                  <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>Median (P50)</th>
                  <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>P75</th>
                  <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>P95</th>
                  <th style={{ padding: '12px 16px', fontSize: '0.875rem' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(categoryBenchmarks).map(([metricKey, dist]: [string, any], idx) => {
                  const isSufficient = dist.is_sufficient && dist.sample_size >= 100;
                  return (
                    <tr
                      key={metricKey}
                      style={{
                        borderBottom: '1px solid var(--color-border)',
                        backgroundColor: idx % 2 === 0 ? 'transparent' : 'var(--color-surface-container)',
                      }}
                    >
                      <td style={{ padding: '12px 16px', fontWeight: 600, textTransform: 'capitalize' }}>
                        {metricKey.replace(/_/g, ' ')}
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--color-text-muted)' }}>
                        <code>{dist.unit}</code>
                      </td>
                      <td style={{ padding: '12px 16px' }}>{dist.sample_size?.toLocaleString()}</td>
                      <td style={{ padding: '12px 16px' }}>{dist.percentiles?.p25?.toFixed(1) ?? '—'}</td>
                      <td style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--color-accent)' }}>
                        {dist.percentiles?.p50?.toFixed(1) ?? '—'}
                      </td>
                      <td style={{ padding: '12px 16px' }}>{dist.percentiles?.p75?.toFixed(1) ?? '—'}</td>
                      <td style={{ padding: '12px 16px' }}>{dist.percentiles?.p95?.toFixed(1) ?? '—'}</td>
                      <td style={{ padding: '12px 16px' }}>
                        <span className={`badge ${isSufficient ? 'badge-favourable' : 'badge-caution'}`}>
                          {isSufficient ? 'Verified n ≥ 100' : 'Limited Data'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Health Considerations Section */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <h2 style={{ marginBottom: 'var(--space-md)' }}>Health Considerations & Risk Factors</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-md)' }}>
          {selectedCategory.healthConsiderations.map((hc, idx) => (
            <div
              key={idx}
              style={{
                padding: 'var(--space-md)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-surface-dim)',
                border: '1px solid var(--color-border)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: 'var(--space-sm)',
              }}
            >
              <div>
                <h4 style={{ marginBottom: '4px' }}>{hc.title}</h4>
                <p style={{ fontSize: '0.875rem', lineHeight: 1.5 }}>{hc.desc}</p>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)', borderTop: '1px solid var(--color-border)', paddingTop: '6px' }}>
                Source: {hc.source} ({hc.year})
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Sources & Citations */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-sm)' }}>
          <BookOpen size={20} color="var(--color-primary)" />
          <h3>Authoritative Citations & References</h3>
        </div>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
          {selectedCategory.sources.map((src, idx) => (
            <li
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--color-surface-container)',
                fontSize: '0.875rem',
              }}
            >
              <div>
                <strong>{src.org}</strong>: {src.title} ({src.year})
              </div>
              <a
                href={src.url}
                target="_blank"
                rel="noreferrer noopener"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  color: 'var(--color-accent)',
                  fontWeight: 600,
                  fontSize: '0.8125rem',
                }}
              >
                <span>View Guidelines</span>
                <ShieldCheck size={14} />
              </a>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};
