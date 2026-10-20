import React, { useState, useEffect } from 'react';
import { useLocation, useSearchParams, Link, useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Printer,
  Sparkles,
  ArrowLeft,
  Info,
  Calendar,
  ExternalLink,
  Award,
  TrendingDown,
  TrendingUp,
  FileText,
} from 'lucide-react';
import { ScoreGauge } from '../components/common/ScoreGauge';
import { GuidelineChart } from '../components/charts/GuidelineChart';
import { BenchmarkRangeChart } from '../components/charts/BenchmarkRangeChart';
import { getHistoryItem } from '../services/historyService';
import { exportReportToPDF } from '../services/pdfService';
import type { ScoringEngineResult } from '../types';

export const ResultPage: React.FC = () => {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [result, setResult] = useState<ScoringEngineResult | null>(null);
  const [reportDate, setReportDate] = useState<string>(new Date().toLocaleString());

  useEffect(() => {
    // 1. Try from location.state
    if (location.state?.result) {
      setResult(location.state.result);
      return;
    }

    // 2. Try from local history query param ?id=...
    const scanId = searchParams.get('id');
    if (scanId) {
      const record = getHistoryItem(scanId);
      if (record && record.result) {
        setResult(record.result);
        setReportDate(new Date(record.timestamp).toLocaleString());
        return;
      }
    }
  }, [location.state, searchParams]);

  if (!result) {
    return (
      <div style={{ maxWidth: '640px', margin: 'var(--space-2xl) auto', textAlign: 'center' }}>
        <div className="card" style={{ padding: 'var(--space-2xl)' }}>
          <FileText size={48} color="var(--color-text-subtle)" style={{ margin: '0 auto var(--space-md)' }} />
          <h2 style={{ marginBottom: 'var(--space-sm)' }}>No Analysis Report Found</h2>
          <p style={{ marginBottom: 'var(--space-lg)' }}>
            No active beverage evaluation was found in memory or stored history for this ID.
          </p>
          <Link to="/lab" className="btn btn-primary">
            <Sparkles size={16} />
            <span>Start New Analysis in Lab</span>
          </Link>
        </div>
      </div>
    );
  }

  const isCritical = result.critical_override?.is_critical || false;
  const isAlcoholic = ['Beer', 'Wine', 'Spirits'].includes(result.beverage_type);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)', maxWidth: '1100px', margin: '0 auto' }}>
      {/* Top Action Bar (hidden when printing PDF) */}
      <div className="no-print" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
        <button
          onClick={() => navigate('/lab')}
          className="btn btn-secondary"
          style={{ padding: '6px 14px' }}
        >
          <ArrowLeft size={16} />
          <span>Analyze Another Drink</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
          <button
            onClick={() => exportReportToPDF()}
            className="btn btn-primary"
            style={{ padding: '6px 16px', backgroundColor: 'var(--color-primary)' }}
          >
            <Printer size={16} />
            <span>Download PDF / Print</span>
          </button>
        </div>
      </div>

      {/* Critical Health Warning Banner */}
      {isCritical && (
        <section
          className="card animate-fade-in"
          style={{
            padding: 'var(--space-lg)',
            backgroundColor: 'var(--color-critical-bg)',
            borderColor: 'var(--color-critical-border)',
            borderLeft: '6px solid var(--color-critical)',
          }}
          role="alert"
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-md)' }}>
            <div style={{ color: 'var(--color-critical)', marginTop: '2px' }}>
              <ShieldAlert size={28} />
            </div>
            <div>
              <h3 style={{ color: 'var(--color-critical-text)', marginBottom: '4px' }}>
                Critical Health Override Triggered (Score Capped at 40)
              </h3>
              <p style={{ color: 'var(--color-critical-text)', fontSize: '0.9375rem', marginBottom: 'var(--space-sm)' }}>
                This beverage contains compound levels that breach authoritative acute or toxicological thresholds:
              </p>
              <ul style={{ paddingLeft: '20px', color: 'var(--color-critical-text)', fontSize: '0.875rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {result.critical_override.critical_reasons.map((reason, idx) => (
                  <li key={idx}><strong>{reason}</strong></li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}

      {/* Partial Analysis Notice */}
      {result.is_partial_analysis && (
        <div
          style={{
            padding: 'var(--space-sm) var(--space-md)',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--color-caution-bg)',
            border: '1px solid var(--color-caution-border)',
            color: 'var(--color-caution-text)',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <AlertTriangle size={18} />
          <span>
            <strong>Partial Analysis Notice:</strong> Some recommended ingredients were omitted ({result.missing_fields.join(', ')}). Confidence is adjusted to {result.confidence_level} ({result.confidence_percentage}%).
          </span>
        </div>
      )}

      {/* Section A: Report Header */}
      <section
        className="glass-panel"
        style={{
          padding: 'var(--space-xl)',
          borderRadius: 'var(--radius-xl)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-lg)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-2xs)' }}>
              <span className="badge badge-neutral">{result.beverage_type}</span>
              <span className={`badge ${result.confidence_level === 'High' ? 'badge-favourable' : 'badge-moderate'}`}>
                {result.confidence_level} Confidence ({result.confidence_percentage}%)
              </span>
              {result.is_partial_analysis && (
                <span className="badge badge-caution">Partial Evaluation</span>
              )}
            </div>

            <h1 style={{ fontSize: '2rem', marginBottom: '4px' }}>
              {result.product_name || `${result.beverage_type} Sample`}
            </h1>

            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', fontSize: '0.875rem', color: 'var(--color-text-subtle)' }}>
              <span>Serving Size: <strong>{result.serving_size_ml} mL</strong></span>
              <span>·</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Calendar size={14} /> {reportDate}
              </span>
              <span>·</span>
              <span>Rules v{result.rules_version} · Data v{result.dataset_version}</span>
            </div>
          </div>

          {/* Alcohol Grams & Standard Drinks Pill */}
          {result.alcohol_grams !== null && result.alcohol_grams !== undefined && (
            <div
              style={{
                padding: 'var(--space-sm) var(--space-md)',
                backgroundColor: 'var(--color-surface-dim)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--color-border)',
                textAlign: 'right',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Calculated Pure Ethanol</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-primary)' }}>
                {result.alcohol_grams.toFixed(1)} g
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>
                ≈ {result.standard_drinks?.toFixed(1)} WHO standard drinks (10g)
              </div>
            </div>
          )}
        </div>

        {/* Strictly Separated Scores Matrix */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 'var(--space-lg)',
            marginTop: 'var(--space-xs)',
          }}
        >
          {/* Health Impact Score */}
          <ScoreGauge
            score={result.health_impact_score}
            uncappedScore={result.uncapped_health_impact_score}
            title="Health Impact Score"
            subtitle="Clinical guideline alignment (WHO, EFSA, JECFA)"
            type="health"
            isCritical={isCritical}
          />

          {/* Composition Score */}
          <ScoreGauge
            score={result.composition_score}
            title="Composition Score"
            subtitle="Empirical nutrient density vs. typical category benchmark"
            type="composition"
          />
        </div>
      </section>

      {/* Mandatory WHO Alcohol Advisory */}
      {isAlcoholic && (
        <div
          className="card"
          style={{
            padding: 'var(--space-md) var(--space-lg)',
            backgroundColor: 'var(--color-surface-container-high)',
            borderLeft: '4px solid var(--color-primary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Info size={18} color="var(--color-primary)" />
            <h4 style={{ fontSize: '0.9375rem' }}>Authoritative Public Health Advisory: Alcohol</h4>
          </div>
          <p style={{ fontSize: '0.875rem', lineHeight: 1.5 }}>
            {result.alcohol_advisory ||
              'The World Health Organization (WHO) affirms that when it comes to alcohol consumption, there is no safe amount that does not affect health. Alcohol is a toxic, psychoactive, and dependence-producing substance classified by IARC as a Group 1 human carcinogen.'}
          </p>
        </div>
      )}

      {/* Section B: Higher and Lower Than Typical Panels */}
      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-md)',
        }}
      >
        {/* Higher Than Typical */}
        <div className="card" style={{ padding: 'var(--space-lg)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-sm)' }}>
            <TrendingUp size={20} color="var(--color-comp-higher)" />
            <h3>Higher Than Typical</h3>
          </div>
          {result.higher_than_typical && result.higher_than_typical.length > 0 ? (
            <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.875rem' }}>
              {result.higher_than_typical.map((item, idx) => (
                <li key={idx} style={{ color: 'var(--color-text-main)' }}>
                  <strong>{item}</strong> sits above the 75th empirical category percentile.
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)' }}>
              No measured ingredients exceed the 75th percentile of typical {result.beverage_type} samples.
            </p>
          )}
        </div>

        {/* Lower Than Typical */}
        <div className="card" style={{ padding: 'var(--space-lg)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-sm)' }}>
            <TrendingDown size={20} color="var(--color-comp-lower)" />
            <h3>Lower Than Typical</h3>
          </div>
          {result.lower_than_typical && result.lower_than_typical.length > 0 ? (
            <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.875rem' }}>
              {result.lower_than_typical.map((item, idx) => (
                <li key={idx} style={{ color: 'var(--color-text-main)' }}>
                  <strong>{item}</strong> is below the 25th empirical category percentile.
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)' }}>
              No measured ingredients are below the 25th percentile of typical {result.beverage_type} samples.
            </p>
          )}
        </div>
      </section>

      {/* Section C: Detailed Ingredient Analysis Table */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)' }}>
          <div>
            <h2>Clinical Ingredient Assessment Matrix</h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)' }}>
              Evaluated against published health guidelines and empirical category distributions.
            </p>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--color-border)', color: 'var(--color-text-subtle)' }}>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>Ingredient</th>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>Serving Amount</th>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>Guideline Limit</th>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>% Daily/Dose Limit</th>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>Band</th>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>Category Benchmark</th>
                <th style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>Source</th>
              </tr>
            </thead>
            <tbody>
              {result.guideline_evaluations.map((ge, idx) => {
                const bm = result.benchmark_evaluations.find(
                  (b) => b.ingredient_key === ge.ingredient_key
                );

                let bandBadge = 'badge-moderate';
                if (ge.band === 'Favourable') bandBadge = 'badge-favourable';
                else if (ge.band === 'Caution') bandBadge = 'badge-caution';
                else if (ge.band === 'High' || ge.is_critical_breach) bandBadge = 'badge-critical';

                const pctLimit = (ge.guideline_ratio * 100).toFixed(0);

                return (
                  <tr
                    key={ge.ingredient_key}
                    style={{
                      borderBottom: '1px solid var(--color-border)',
                      backgroundColor: idx % 2 === 0 ? 'transparent' : 'var(--color-surface-container)',
                    }}
                  >
                    <td style={{ padding: '12px 14px', fontWeight: 600 }}>{ge.ingredient_name}</td>
                    <td style={{ padding: '12px 14px' }}>
                      <strong>{ge.amount_per_serving} {ge.unit}</strong>
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--color-text-muted)' }}>
                      {ge.guideline_limit} {ge.unit}
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 600 }}>
                      {pctLimit}%
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={`badge ${bandBadge}`}>{ge.band}</span>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>
                      {bm ? (
                        <span style={{ textTransform: 'capitalize' }}>
                          {bm.status.replace(/_/g, ' ')} (n={bm.sample_size})
                        </span>
                      ) : (
                        <span style={{ color: 'var(--color-text-subtle)' }}>Not evaluated</span>
                      )}
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: '0.8125rem' }}>
                      <a
                        href={ge.source_url}
                        target="_blank"
                        rel="noreferrer noopener"
                        style={{ color: 'var(--color-accent)', display: 'inline-flex', alignItems: 'center', gap: '3px' }}
                      >
                        <span>{ge.source_organization} ({ge.publication_year || 'Ref'})</span>
                        <ExternalLink size={12} />
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Section D: Health Impact Explanations */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <h2 style={{ marginBottom: 'var(--space-md)' }}>Health Impact Mechanisms & Evidence</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--space-md)' }}>
          {result.guideline_evaluations.map((ge) => (
            <div
              key={ge.ingredient_key}
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <h4 style={{ fontSize: '1rem' }}>{ge.ingredient_name}</h4>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-subtle)' }}>
                    {ge.source_organization}
                  </span>
                </div>
                <p style={{ fontSize: '0.875rem', lineHeight: 1.5 }}>
                  {ge.rationale}
                </p>
              </div>

              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)', borderTop: '1px solid var(--color-border)', paddingTop: '6px' }}>
                Threshold basis: {ge.guideline_limit} {ge.unit} per evaluation rule.
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Section E: Benchmark Visualizations */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
        <GuidelineChart evaluations={result.guideline_evaluations} />
        <BenchmarkRangeChart
          benchmarks={result.benchmark_evaluations}
          categoryName={result.beverage_type}
        />
      </section>

      {/* Section F: Wine Sensory Quality ML Model (Wine Only) */}
      {result.beverage_type === 'Wine' && (
        <section
          className="card"
          style={{
            padding: 'var(--space-xl)',
            borderLeft: '4px solid #8B5CF6',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-sm)' }}>
            <Award size={24} color="#8B5CF6" />
            <div>
              <h3>Portuguese Vinho Verde Sensory Quality Prediction</h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
                Machine Learning regressor trained on UCI Wine Quality dataset (Cortez et al., 2009).
              </p>
            </div>
          </div>

          {result.wine_model?.is_available ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)', marginTop: 'var(--space-sm)' }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
                <span style={{ fontSize: '2.5rem', fontWeight: 800, color: '#8B5CF6' }}>
                  {(result.wine_model.predicted_quality || result.wine_model.predicted_rating || 0).toFixed(1)}
                </span>
                <span style={{ fontSize: '1rem', color: 'var(--color-text-subtle)' }}>
                  / 10.0 (Expert Panel Sensory Rating Scale: 0 to 10)
                </span>
              </div>
              {result.wine_model.test_mae !== null && result.wine_model.test_mae !== undefined && (
                <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
                  Model Accuracy: <strong>Held-out test split MAE ±{result.wine_model.test_mae.toFixed(2)} rating points</strong>
                </div>
              )}
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                {result.wine_model.model_limitations ||
                  'The model predicts sensory quality scores as evaluated by certified wine tasting panels for Portuguese Vinho Verde wines. Note: This is an organoleptic quality rating and NOT a health score.'}
              </p>
            </div>
          ) : (
            <div style={{ padding: 'var(--space-md)', backgroundColor: 'var(--color-surface-dim)', borderRadius: 'var(--radius-md)' }}>
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                ⚠️ {result.wine_model?.reason_if_unavailable || 'Sensory quality prediction requires all 11 physicochemical inputs (fixed acidity, volatile acidity, citric acid, residual sugar, chlorides, free SO2, total SO2, density, pH, sulphates, alcohol). Basic analysis completed.'}
              </p>
            </div>
          )}
        </section>
      )}

      {/* Section H: Mandatory Scientific & Clinical Disclaimer */}
      <section
        style={{
          padding: 'var(--space-lg)',
          backgroundColor: 'var(--color-surface-container)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <ShieldCheck size={18} color="var(--color-text-subtle)" />
          <h4 style={{ fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Mandatory Clinical & Regulatory Disclaimer
          </h4>
        </div>
        <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
          {result.disclaimer ||
            'This report is for informational and educational purposes only and is not medical advice. Results depend on the values entered and the available reference data, which may contain errors or gaps. This application does not measure beverages or replace laboratory testing or professional advice.'}
        </p>
      </section>
    </div>
  );
};
