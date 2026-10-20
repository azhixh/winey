import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  X,
  Layers,
  BookOpen,
  History,
  Package,
  ArrowRight,
  AlertCircle,
} from 'lucide-react';
import { getHistory } from '../services/historyService';
import { searchProducts } from '../services/api';
import type { HistoryRecord } from '../types';

interface IngredientGlossaryItem {
  name: string;
  category: string;
  desc: string;
  threshold: string;
  source: string;
}

const INGREDIENT_GLOSSARY: IngredientGlossaryItem[] = [
  {
    name: 'Free Sugars',
    category: 'Soft Drinks & Energy Drinks',
    desc: 'All monosaccharides and disaccharides added to foods plus sugars naturally present in honey, syrups, and fruit juices. Associated with dental caries, cardiovascular risk, and obesity.',
    threshold: 'WHO 25g/day ideal, 50g/day cap',
    source: 'WHO Sugars Guideline (2015)',
  },
  {
    name: 'Caffeine',
    category: 'Energy Drinks & Soft Drinks',
    desc: 'Central nervous system stimulant that reversibly antagonizes adenosine receptors. High doses cause tachycardia, autonomic arousal, and insomnia.',
    threshold: 'EFSA 200mg single dose, 400mg/day (3 mg/kg for minors)',
    source: 'EFSA Caffeine Opinion (2015)',
  },
  {
    name: 'Sodium Benzoate (E211)',
    category: 'Soft Drinks',
    desc: 'Antimicrobial food preservative converted to benzoic acid in the stomach. High concentrations evaluated for potential hyperreactivity.',
    threshold: 'JECFA ADI 5 mg/kg body weight',
    source: 'FAO/WHO JECFA (2021)',
  },
  {
    name: 'Sulphites as SO2',
    category: 'Beer & Wine',
    desc: 'Sulfur dioxide and sulfite salts used as antioxidants and microbial inhibitors. In sulfite-sensitive asthmatics, even low levels can trigger acute bronchospasm.',
    threshold: 'EFSA ADI 0.7 mg/kg body weight',
    source: 'EFSA Re-evaluation of Sulfites (2016)',
  },
  {
    name: 'Methanol',
    category: 'Spirits & Alcohol',
    desc: 'Toxic congener formed during pectin breakdown. Metabolized to formaldehyde and formic acid, causing metabolic acidosis and irreversible blindness.',
    threshold: 'EU Regulation 2019/787: Max 10.0 g/L pure alcohol',
    source: 'EU Regulation 2019/787',
  },
  {
    name: 'Taurine',
    category: 'Energy Drinks',
    desc: 'Conditionally essential amino sulfonic acid added to energy drinks. Not associated with toxicological adverse effects up to 1000 mg/serving.',
    threshold: 'EFSA 1000 mg/serving no-adverse threshold',
    source: 'EFSA Journal (2009)',
  },
  {
    name: 'Phosphoric Acid',
    category: 'Soft Drinks',
    desc: 'Acidulant giving cola beverages sharp flavor. High consumption associated with lower bone mineral density and tooth erosion.',
    threshold: 'EFSA Phosphate ADI 40 mg/kg body weight',
    source: 'EFSA Phosphate Re-evaluation (2019)',
  },
];

const BEVERAGE_CATEGORIES_SEARCH = [
  { name: 'Soft Drinks', path: '/drinks/soft-drinks', desc: 'Free sugars, calories, caffeine, sodium benzoate, and pH balance.' },
  { name: 'Beer & Ales', path: '/drinks/beer', desc: 'Alcohol ABV, carbohydrate load, sulphite ADI, and standard drinks.' },
  { name: 'Energy Drinks', path: '/drinks/energy-drinks', desc: 'Acute single-dose caffeine, daily stimulant caps, and taurine.' },
  { name: 'Wine (Red & White)', path: '/drinks/wine', desc: 'Residual sugar, total SO2, acidity balance, and UCI ML sensory quality prediction.' },
  { name: 'Alcohol / Spirits', path: '/drinks/alcohol', desc: 'Distilled ethanol strength, standard drink equivalents, and toxic methanol limits.' },
];

export const SearchPage: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [localHistory, setLocalHistory] = useState<HistoryRecord[]>([]);
  const [apiResults, setApiResults] = useState<any[]>([]);
  const [apiLoading, setApiLoading] = useState<boolean>(false);
  const [apiUnavailable, setApiUnavailable] = useState<boolean>(false);

  useEffect(() => {
    setLocalHistory(getHistory());
  }, []);

  // External product search via API with debounce
  useEffect(() => {
    if (!query.trim() || query.length < 3) {
      setApiResults([]);
      setApiUnavailable(false);
      return;
    }

    const timer = setTimeout(async () => {
      setApiLoading(true);
      try {
        const res = await searchProducts(query);
        if (res && Array.isArray(res.products)) {
          setApiResults(res.products);
          setApiUnavailable(false);
        } else if (Array.isArray(res)) {
          setApiResults(res);
          setApiUnavailable(false);
        } else {
          setApiResults([]);
        }
      } catch (e) {
        setApiResults([]);
        setApiUnavailable(true);
      } finally {
        setApiLoading(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [query]);

  const q = query.toLowerCase().trim();

  // Filter local categories
  const matchingCategories = q
    ? BEVERAGE_CATEGORIES_SEARCH.filter(
        (c) => c.name.toLowerCase().includes(q) || c.desc.toLowerCase().includes(q)
      )
    : [];

  // Filter ingredient glossary
  const matchingGlossary = q
    ? INGREDIENT_GLOSSARY.filter(
        (g) =>
          g.name.toLowerCase().includes(q) ||
          g.desc.toLowerCase().includes(q) ||
          g.category.toLowerCase().includes(q)
      )
    : [];

  // Filter local history
  const matchingHistory = q
    ? localHistory.filter(
        (h) =>
          h.product_name.toLowerCase().includes(q) ||
          h.beverage_type.toLowerCase().includes(q)
      )
    : [];

  const hasAnyResults =
    matchingCategories.length > 0 ||
    matchingGlossary.length > 0 ||
    matchingHistory.length > 0 ||
    apiResults.length > 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)', maxWidth: '960px', margin: '0 auto' }}>
      {/* Search Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <Search size={24} color="var(--color-accent)" />
          <h1>Search Beverage Intelligence</h1>
        </div>
        <p>
          Search across beverage categories, clinical ingredient definitions, previous local analyses, and external nutritional registries.
        </p>
      </div>

      {/* Search Input Box */}
      <div className="card" style={{ padding: 'var(--space-md)' }}>
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <Search
            size={20}
            color="var(--color-text-subtle)"
            style={{ position: 'absolute', left: '14px', pointerEvents: 'none' }}
          />
          <input
            type="text"
            className="form-input"
            style={{
              paddingLeft: '44px',
              paddingRight: query ? '44px' : '16px',
              fontSize: '1.0625rem',
              height: '48px',
            }}
            placeholder="Search by ingredient, category, drink name, or guideline (e.g. caffeine, wine, sugar)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="btn btn-ghost"
              style={{ position: 'absolute', right: '10px', padding: '6px' }}
              aria-label="Clear search input"
            >
              <X size={18} />
            </button>
          )}
        </div>
      </div>

      {/* When Query is Empty */}
      {!q && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          <div className="card" style={{ padding: 'var(--space-xl)' }}>
            <h3 style={{ marginBottom: 'var(--space-sm)' }}>Popular Search Topics</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {['Caffeine', 'Free Sugars', 'Methanol', 'Sulphites', 'Beer', 'Wine', 'Energy Drink', 'Sodium Benzoate'].map(
                (topic) => (
                  <button
                    key={topic}
                    onClick={() => setQuery(topic)}
                    className="btn btn-secondary"
                    style={{ borderRadius: 'var(--radius-pill)', padding: '6px 14px', fontSize: '0.875rem' }}
                  >
                    {topic}
                  </button>
                )
              )}
            </div>
          </div>

          {/* Quick Category Directory */}
          <div className="card" style={{ padding: 'var(--space-xl)' }}>
            <h3 style={{ marginBottom: 'var(--space-md)' }}>All Categories</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--space-sm)' }}>
              {BEVERAGE_CATEGORIES_SEARCH.map((cat) => (
                <Link
                  key={cat.name}
                  to={cat.path}
                  style={{
                    padding: 'var(--space-sm) var(--space-md)',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--color-surface-dim)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: '0.9375rem' }}>{cat.name}</span>
                  <ArrowRight size={14} color="var(--color-accent)" />
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* When Query is Entered */}
      {q && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
          {/* No Results Fallback */}
          {!hasAnyResults && !apiLoading && (
            <div className="card" style={{ padding: 'var(--space-2xl)', textAlign: 'center' }}>
              <AlertCircle size={40} color="var(--color-text-subtle)" style={{ margin: '0 auto var(--space-sm)' }} />
              <h3 style={{ marginBottom: 'var(--space-xs)' }}>No results found for "{query}"</h3>
              <p style={{ maxWidth: '440px', margin: '0 auto var(--space-md)' }}>
                We could not find matching categories, clinical glossary definitions, or saved reports.
              </p>
              <button onClick={() => setQuery('')} className="btn btn-secondary">
                Clear Search
              </button>
            </div>
          )}

          {/* Matching Categories */}
          {matchingCategories.length > 0 && (
            <section className="card" style={{ padding: 'var(--space-lg)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-md)' }}>
                <Layers size={18} color="var(--color-accent)" />
                <h3>Beverage Categories ({matchingCategories.length})</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                {matchingCategories.map((cat) => (
                  <Link
                    key={cat.name}
                    to={cat.path}
                    style={{
                      padding: 'var(--space-md)',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--color-surface-dim)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <h4 style={{ fontSize: '1rem', marginBottom: '2px' }}>{cat.name}</h4>
                      <p style={{ fontSize: '0.8125rem' }}>{cat.desc}</p>
                    </div>
                    <ArrowRight size={16} color="var(--color-accent)" />
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Matching Ingredient Glossary */}
          {matchingGlossary.length > 0 && (
            <section className="card" style={{ padding: 'var(--space-lg)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-md)' }}>
                <BookOpen size={18} color="var(--color-primary)" />
                <h3>Clinical Ingredients & Guidelines ({matchingGlossary.length})</h3>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-md)' }}>
                {matchingGlossary.map((item) => (
                  <div
                    key={item.name}
                    style={{
                      padding: 'var(--space-md)',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--color-surface-dim)',
                      border: '1px solid var(--color-border)',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      gap: 'var(--space-xs)',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                        <h4 style={{ fontSize: '1rem' }}>{item.name}</h4>
                        <span style={{ fontSize: '0.6875rem', color: 'var(--color-text-subtle)' }}>{item.category}</span>
                      </div>
                      <p style={{ fontSize: '0.8125rem', lineHeight: 1.4 }}>{item.desc}</p>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-accent)', fontWeight: 600, borderTop: '1px solid var(--color-border)', paddingTop: '6px' }}>
                      {item.threshold} ({item.source})
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Matching Local History */}
          {matchingHistory.length > 0 && (
            <section className="card" style={{ padding: 'var(--space-lg)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-md)' }}>
                <History size={18} color="var(--color-accent)" />
                <h3>Your Previous Analyses ({matchingHistory.length})</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                {matchingHistory.map((item) => (
                  <Link
                    key={item.id}
                    to={`/result?id=${item.id}`}
                    style={{
                      padding: 'var(--space-sm) var(--space-md)',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--color-surface-dim)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <span style={{ fontWeight: 600 }}>{item.product_name}</span>
                      <span style={{ marginLeft: '8px', fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
                        {item.beverage_type} · {new Date(item.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-accent)' }}>
                      View Report →
                    </span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* External Registry Product Search */}
          {q.length >= 3 && (
            <section className="card" style={{ padding: 'var(--space-lg)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-sm)' }}>
                <Package size={18} color="var(--color-primary)" />
                <h3>External Registry Search (Open Food Facts / USDA FoodData)</h3>
              </div>

              {apiLoading ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)' }}>
                  Searching public registry datasets...
                </p>
              ) : apiUnavailable ? (
                <div style={{ padding: 'var(--space-sm) var(--space-md)', backgroundColor: 'var(--color-surface-dim)', borderRadius: 'var(--radius-md)', fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
                  External product lookup is currently offline or unreachable. Manual lab input is always functional.
                </div>
              ) : apiResults.length === 0 ? (
                <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
                  No external packaged products returned for "{query}". You can analyze custom formulas in the Lab.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
                  {apiResults.slice(0, 5).map((p, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: 'var(--space-sm)',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--color-surface-container)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <strong>{p.product_name || p.name || 'Unnamed Product'}</strong>
                        <span style={{ marginLeft: '8px', fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
                          {p.brands || p.category || ''}
                        </span>
                      </div>
                      <Link
                        to={`/lab?category=${encodeURIComponent(p.beverage_type || 'Soft drink')}`}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                      >
                        Analyze in Lab
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      )}
    </div>
  );
};
