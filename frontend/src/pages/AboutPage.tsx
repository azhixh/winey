import React from 'react';
import {
  ShieldCheck,
  Award,
  HeartPulse,
  BarChart3,
  ExternalLink,
  AlertTriangle,
  Scale,
  Database,
} from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2xl)', maxWidth: '960px', margin: '0 auto' }}>
      {/* Page Header */}
      <section
        className="glass-panel"
        style={{
          padding: 'var(--space-2xl) var(--space-xl)',
          borderRadius: 'var(--radius-xl)',
        }}
      >
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', borderRadius: 'var(--radius-pill)', backgroundColor: 'var(--color-accent-subtle)', color: 'var(--color-accent)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: 'var(--space-md)' }}>
          <ShieldCheck size={14} />
          <span>System Version 1.0.0 · Rules v1.0.0 · Data v1.0.0</span>
        </div>
        <h1 style={{ marginBottom: 'var(--space-md)' }}>
          Beverage Quality Analysis System (BQAS)
        </h1>
        <p style={{ fontSize: '1.125rem', lineHeight: 1.6 }}>
          An evidence-based beverage intelligence platform providing clinical guideline evaluations, empirical nutritional benchmark distributions, and machine-learning sensory analytics for consumers, researchers, and beverage developers.
        </p>
      </section>

      {/* Purpose & Principles */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <h2 style={{ marginBottom: 'var(--space-md)' }}>Core Scientific Principles</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--space-lg)' }}>
          <div>
            <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <Scale size={18} color="var(--color-primary)" />
              <span>Evidence-Based Only</span>
            </h4>
            <p style={{ fontSize: '0.875rem', lineHeight: 1.5 }}>
              All scoring thresholds and penalty curves are derived directly from published guidelines established by international public health authorities (WHO, EFSA, FDA, JECFA/Codex).
            </p>
          </div>

          <div>
            <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <ShieldCheck size={18} color="var(--color-accent)" />
              <span>Zero Null Imputation</span>
            </h4>
            <p style={{ fontSize: '0.875rem', lineHeight: 1.5 }}>
              Missing or unquantified fields remain missing and are never converted to zero. Partial analyses reflect transparent confidence levels rather than misleading fabricated perfect scores.
            </p>
          </div>

          <div>
            <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <BarChart3 size={18} color="var(--color-favourable)" />
              <span>Strict Sample Thresholds</span>
            </h4>
            <p style={{ fontSize: '0.875rem', lineHeight: 1.5 }}>
              Empirical benchmark percentiles require at least 100 valid, deduplicated category samples before percentiles are generated to prevent skewed baseline statistics.
            </p>
          </div>
        </div>
      </section>

      {/* Health Impact Score vs Composition Score */}
      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-lg)',
        }}
      >
        <div className="card" style={{ padding: 'var(--space-xl)', borderLeft: '4px solid var(--color-primary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-sm)' }}>
            <HeartPulse size={24} color="var(--color-primary)" />
            <h3>Health Impact Score</h3>
          </div>
          <p style={{ fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: 'var(--space-md)' }}>
            Evaluates the direct clinical risk posed by a beverage per serving relative to authoritative daily boundaries:
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '0.875rem', color: 'var(--color-text-muted)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <li><strong>0 to 100 Clinical Scale</strong>: Higher indicates safer profile with lower guideline ratios.</li>
            <li><strong>Piecewise 5-Band Curve</strong>: Favourable (&le; 0.5 ratio), Moderate (0.5 - 1.0), Caution (1.0 - 2.0), High (&gt; 2.0).</li>
            <li><strong>Critical Overrides</strong>: Capped at 40 upon acute caffeine overdose (&gt; 200mg or 3 mg/kg) or toxic methanol contamination (&gt; 10 g/L pure alcohol).</li>
            <li><strong>Weighted Formulation</strong>: Weighted sum of applicable subscores based on configured clinical priorities.</li>
          </ul>
        </div>

        <div className="card" style={{ padding: 'var(--space-xl)', borderLeft: '4px solid var(--color-accent)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-sm)' }}>
            <BarChart3 size={24} color="var(--color-accent)" />
            <h3>Composition Score</h3>
          </div>
          <p style={{ fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: 'var(--space-md)' }}>
            Compares where your sample sits along the distribution of existing marketplace products:
          </p>
          <ul style={{ paddingLeft: '20px', fontSize: '0.875rem', color: 'var(--color-text-muted)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <li><strong>0 to 100 Empirical Scale</strong>: Measures nutrient density relative to peers.</li>
            <li><strong>Percentile Spectrum</strong>: Lower than typical (&lt; P25), Typical (P25 - P75), Higher (P75 - P95), and Very High (&gt; P95).</li>
            <li><strong>Direction-Aware Credits</strong>: Low sugar receives favorable credits (100 pts), while low calcium/protein receives lower credits.</li>
            <li><strong>Separation Guarantee</strong>: Health Impact Score and Composition Score are never combined or averaged into a single number.</li>
          </ul>
        </div>
      </section>

      {/* Machine Learning Model: Vinho Verde Quality */}
      <section className="card" style={{ padding: 'var(--space-xl)', borderLeft: '4px solid #8B5CF6' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-xs)' }}>
          <Award size={24} color="#8B5CF6" />
          <h3>Portuguese Vinho Verde Wine Quality Model</h3>
        </div>
        <p style={{ fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: 'var(--space-md)' }}>
          BQAS features a scikit-learn regressor trained on the official University of California Irvine (UCI) Wine Quality dataset (Cortez et al., 2009).
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--space-md)', backgroundColor: 'var(--color-surface-dim)', padding: 'var(--space-md)', borderRadius: 'var(--radius-md)' }}>
          <div>
            <strong>Training Dataset:</strong>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
              1,599 red and 4,898 white wine samples from the Vinho Verde region in northwest Portugal.
            </p>
          </div>
          <div>
            <strong>11 Input Features:</strong>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
              Fixed acidity, volatile acidity, citric acid, residual sugar, chlorides, free SO2, total SO2, density, pH, sulphates, alcohol.
            </p>
          </div>
          <div>
            <strong>Important Limitation:</strong>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
              Predicts expert panel sensory ratings (0 to 10 scale). It is an organoleptic taste score and NOT a health score.
            </p>
          </div>
        </div>
      </section>

      {/* Data Sources and Licenses */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-md)' }}>
          <Database size={20} color="var(--color-primary)" />
          <h2>Data Sources & Attribution</h2>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--color-border)', color: 'var(--color-text-subtle)' }}>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>Source Organization</th>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>Resource / Dataset</th>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>License</th>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>Reference Link</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '12px 14px', fontWeight: 600 }}>World Health Organization (WHO)</td>
                <td style={{ padding: '12px 14px' }}>Sugars Intake Guidelines & Alcohol Facts</td>
                <td style={{ padding: '12px 14px' }}>Public Information</td>
                <td style={{ padding: '12px 14px' }}>
                  <a href="https://www.who.int" target="_blank" rel="noreferrer" style={{ color: 'var(--color-accent)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    who.int <ExternalLink size={12} />
                  </a>
                </td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '12px 14px', fontWeight: 600 }}>European Food Safety Authority (EFSA)</td>
                <td style={{ padding: '12px 14px' }}>Caffeine, Sulphites, Benzoates Opinions</td>
                <td style={{ padding: '12px 14px' }}>Open Access (CC BY 4.0)</td>
                <td style={{ padding: '12px 14px' }}>
                  <a href="https://www.efsa.europa.eu" target="_blank" rel="noreferrer" style={{ color: 'var(--color-accent)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    efsa.europa.eu <ExternalLink size={12} />
                  </a>
                </td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '12px 14px', fontWeight: 600 }}>UCI Machine Learning Repository</td>
                <td style={{ padding: '12px 14px' }}>Wine Quality Dataset (Cortez et al., 2009)</td>
                <td style={{ padding: '12px 14px' }}>CC BY 4.0</td>
                <td style={{ padding: '12px 14px' }}>
                  <a href="https://archive.ics.uci.edu/dataset/186/wine+quality" target="_blank" rel="noreferrer" style={{ color: 'var(--color-accent)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    archive.ics.uci.edu <ExternalLink size={12} />
                  </a>
                </td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '12px 14px', fontWeight: 600 }}>USDA FoodData Central</td>
                <td style={{ padding: '12px 14px' }}>Nutritional Baseline Distributions</td>
                <td style={{ padding: '12px 14px' }}>Public Domain</td>
                <td style={{ padding: '12px 14px' }}>
                  <a href="https://fdc.nal.usda.gov" target="_blank" rel="noreferrer" style={{ color: 'var(--color-accent)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    fdc.nal.usda.gov <ExternalLink size={12} />
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Mandatory Disclaimer */}
      <section
        style={{
          padding: 'var(--space-lg)',
          backgroundColor: 'var(--color-surface-container)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <AlertTriangle size={18} color="var(--color-text-subtle)" />
          <h4 style={{ fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Clinical & Informational Disclaimer
          </h4>
        </div>
        <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
          This report is for informational and educational purposes only and is not medical advice. Results depend on the values entered and the available reference data, which may contain errors or gaps. This application does not measure beverages or replace laboratory testing or professional advice.
        </p>
      </section>
    </div>
  );
};
