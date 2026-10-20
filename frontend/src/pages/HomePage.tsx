import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  BarChart3,
  HeartPulse,
  Coffee,
  Beer,
  Zap,
  Wine,
  Flame,
  Clock,
} from 'lucide-react';
import { getHistory } from '../services/historyService';
import type { HistoryRecord } from '../types';

export const HomePage: React.FC = () => {
  const [recentScans, setRecentScans] = useState<HistoryRecord[]>([]);

  useEffect(() => {
    setRecentScans(getHistory().slice(0, 3));
  }, []);

  const beverageCategories = [
    {
      id: 'soft-drinks',
      name: 'Soft Drinks',
      desc: 'Colas, sodas, and carbonated beverages evaluated for free sugars and E211.',
      icon: Coffee,
      color: '#3B82F6',
      sampleCount: '1,420 records',
    },
    {
      id: 'beer',
      name: 'Beer & Ales',
      desc: 'Lagers, ales, and stouts assessed for ABV, carbohydrates, and sulphite ADI.',
      icon: Beer,
      color: '#F59E0B',
      sampleCount: '890 records',
    },
    {
      id: 'energy-drinks',
      name: 'Energy Drinks',
      desc: 'Functional stimulants tested against EFSA acute and daily caffeine bounds.',
      icon: Zap,
      color: '#10B981',
      sampleCount: '640 records',
    },
    {
      id: 'wine',
      name: 'Wine (Red & White)',
      desc: 'Residual sugar, SO2 benchmarks, and UCI Vinho Verde ML sensory quality prediction.',
      icon: Wine,
      color: '#8B5CF6',
      sampleCount: '6,497 samples',
    },
    {
      id: 'alcohol',
      name: 'Alcohol / Spirits',
      desc: 'High-proof spirits, ethanol volume, WHO standard drinks, and critical methanol limits.',
      icon: Flame,
      color: '#EF4444',
      sampleCount: '512 records',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2xl)' }}>
      {/* Hero Section */}
      <section
        className="glass-panel"
        style={{
          padding: 'var(--space-2xl) var(--space-xl)',
          borderRadius: 'var(--radius-xl)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ maxWidth: '800px' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 12px',
              borderRadius: 'var(--radius-pill)',
              backgroundColor: 'var(--color-accent-subtle)',
              color: 'var(--color-accent)',
              fontSize: '0.8125rem',
              fontWeight: 600,
              marginBottom: 'var(--space-md)',
            }}
          >
            <ShieldCheck size={14} />
            <span>PRD Section 12 Deterministic Scoring Engine</span>
          </div>

          <h1 style={{ marginBottom: 'var(--space-md)' }}>
            Evidence-Based Beverage Intelligence & Chemical Analytics
          </h1>

          <p style={{ fontSize: '1.125rem', lineHeight: 1.6, marginBottom: 'var(--space-xl)' }}>
            Analyze nutritional density, guideline compliance, and empirical benchmark percentiles across packaged sodas, beers, wines, spirits, and energy drinks without subjective scoring or zero-imputation.
          </p>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
            <Link to="/lab" className="btn btn-primary" style={{ padding: '0.75rem 1.75rem', fontSize: '1rem' }}>
              <Sparkles size={18} />
              <span>Analyze a Beverage</span>
              <ArrowRight size={18} />
            </Link>

            <Link to="/about" className="btn btn-secondary" style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}>
              <span>Methodology & Evidence</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Beverage Categories Matrix */}
      <section>
        <div style={{ marginBottom: 'var(--space-lg)' }}>
          <h2>Supported Beverage Categories</h2>
          <p>
            Select a category to explore empirical benchmark percentiles, guideline thresholds, and chemical profiles.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: 'var(--space-md)',
          }}
        >
          {beverageCategories.map((cat) => {
            const Icon = cat.icon;
            return (
              <Link
                key={cat.id}
                to={`/drinks/${cat.id}`}
                className="card"
                style={{
                  padding: 'var(--space-lg)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: 'var(--space-md)',
                  textDecoration: 'none',
                }}
              >
                <div>
                  <div
                    style={{
                      width: '44px',
                      height: '44px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--color-surface-dim)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: cat.color,
                      marginBottom: 'var(--space-sm)',
                    }}
                  >
                    <Icon size={24} />
                  </div>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: 'var(--space-2xs)' }}>{cat.name}</h3>
                  <p style={{ fontSize: '0.875rem' }}>{cat.desc}</p>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingTop: 'var(--space-sm)',
                    borderTop: '1px solid var(--color-border)',
                  }}
                >
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
                    {cat.sampleCount}
                  </span>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-accent)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    View Matrix <ArrowRight size={14} />
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Score Architecture Explanation: Health vs Composition */}
      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-lg)',
        }}
      >
        {/* Health Impact Score Explainer */}
        <div className="card" style={{ padding: 'var(--space-xl)', borderLeft: '4px solid var(--color-primary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginBottom: 'var(--space-sm)' }}>
            <HeartPulse size={24} color="var(--color-primary)" />
            <h3>Health Impact Score</h3>
          </div>
          <p style={{ fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: 'var(--space-md)' }}>
            A strict, guideline-weighted clinical evaluation comparing ingredient doses against authoritative published boundaries (WHO free sugars 25g/50g, EFSA caffeine 200mg/400mg, JECFA sodium benzoate ADI).
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '0.875rem', color: 'var(--color-text-muted)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <li>Piecewise 5-band mathematical penalty curve (0 to 100).</li>
            <li>Critical Overrides: Caps score at 40 upon acute caffeine or toxic methanol breach.</li>
            <li>Personalized for minors, pregnancy, and body weight.</li>
          </ul>
        </div>

        {/* Composition Score Explainer */}
        <div className="card" style={{ padding: 'var(--space-xl)', borderLeft: '4px solid var(--color-accent)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginBottom: 'var(--space-sm)' }}>
            <BarChart3 size={24} color="var(--color-accent)" />
            <h3>Composition Score</h3>
          </div>
          <p style={{ fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: 'var(--space-md)' }}>
            An independent empirical benchmark score that measures where your sample sits relative to typical products in its category (Open Food Facts, USDA FoodData Central).
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '0.875rem', color: 'var(--color-text-muted)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <li>Categorized into P25 (Lower), Typical (P25 - P75), and P95 (Very High).</li>
            <li>Credits awarded based on nutrient risk direction (e.g. low sugar is favorable).</li>
            <li>Requires at least 100 valid sample records before percentiles are calculated.</li>
          </ul>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <h2 style={{ marginBottom: 'var(--space-lg)' }}>How the Analysis Engine Works</h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: 'var(--space-lg)',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontWeight: 800, fontSize: '1.25rem', color: 'var(--color-accent)' }}>01</span>
              <h4>Unit Normalization</h4>
            </div>
            <p style={{ fontSize: '0.875rem' }}>
              Per-serving and per-100-ml metrics are standardized. Alcohol grams are calculated via pure ethanol density (0.789 g/mL) and standard drinks (10g WHO default).
            </p>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontWeight: 800, fontSize: '1.25rem', color: 'var(--color-accent)' }}>02</span>
              <h4>Null Value Safety</h4>
            </div>
            <p style={{ fontSize: '0.875rem' }}>
              Omitted or unquantified fields remain missing and are never imputed as zero. Confidence is evaluated based on completed weighted fields.
            </p>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontWeight: 800, fontSize: '1.25rem', color: 'var(--color-accent)' }}>03</span>
              <h4>Score Separation</h4>
            </div>
            <p style={{ fontSize: '0.875rem' }}>
              Health Impact Score and Composition Score remain completely distinct. They are never averaged or substituted for one another.
            </p>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontWeight: 800, fontSize: '1.25rem', color: 'var(--color-accent)' }}>04</span>
              <h4>Wine Quality ML</h4>
            </div>
            <p style={{ fontSize: '0.875rem' }}>
              Wines with 11 physicochemical inputs receive an empirical sensory rating from the Portuguese Vinho Verde machine learning regressor.
            </p>
          </div>
        </div>
      </section>

      {/* Recent Local Guest Scans */}
      {recentScans.length > 0 && (
        <section>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)' }}>
            <h2>Recent Local Analyses</h2>
            <Link to="/history" style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-accent)' }}>
              View All History →
            </Link>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-md)' }}>
            {recentScans.map((scan) => (
              <div key={scan.id} className="card" style={{ padding: 'var(--space-md)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-xs)' }}>
                  <div>
                    <h4 style={{ fontSize: '1rem', marginBottom: '2px' }}>{scan.product_name}</h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
                      {scan.beverage_type} · {scan.serving_size_ml} mL
                    </span>
                  </div>
                  <span className={`badge ${scan.confidence_level === 'High' ? 'badge-favourable' : 'badge-moderate'}`}>
                    {scan.confidence_level} Conf.
                  </span>
                </div>

                <div style={{ display: 'flex', gap: 'var(--space-md)', margin: 'var(--space-sm) 0' }}>
                  <div>
                    <span style={{ fontSize: '0.6875rem', color: 'var(--color-text-subtle)', display: 'block' }}>Health Score</span>
                    <strong style={{ fontSize: '1.125rem', color: 'var(--color-primary)' }}>
                      {scan.health_impact_score !== null && scan.health_impact_score !== undefined
                        ? scan.health_impact_score.toFixed(0)
                        : '—'}
                    </strong>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.6875rem', color: 'var(--color-text-subtle)', display: 'block' }}>Comp Score</span>
                    <strong style={{ fontSize: '1.125rem', color: 'var(--color-accent)' }}>
                      {scan.composition_score !== null && scan.composition_score !== undefined
                        ? scan.composition_score.toFixed(0)
                        : '—'}
                    </strong>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'var(--space-xs)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} /> {new Date(scan.timestamp).toLocaleDateString()}
                  </span>
                  <Link to={`/result?id=${scan.id}`} style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-accent)' }}>
                    Open Report →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
