import React from 'react';
import type { IngredientBenchmark } from '../../types';

interface BenchmarkRangeChartProps {
  benchmarks: IngredientBenchmark[];
  categoryName: string;
}

export const BenchmarkRangeChart: React.FC<BenchmarkRangeChartProps> = ({
  benchmarks,
  categoryName,
}) => {
  if (!benchmarks || benchmarks.length === 0) {
    return (
      <div className="card" style={{ padding: 'var(--space-lg)', textAlign: 'center' }}>
        <p style={{ color: 'var(--color-text-subtle)' }}>
          No category benchmark distributions available for this beverage type.
        </p>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: 'var(--space-lg)' }}>
      <div style={{ marginBottom: 'var(--space-md)' }}>
        <h3>Category Benchmark Ranges</h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)' }}>
          Comparing nutrient density per 100 mL against empirical {categoryName} records (n ≥ 100).
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
        {benchmarks.map((bm) => {
          const isLimited = !bm.is_sufficient || bm.status === 'limited_benchmark_data';

          let statusBadgeClass = 'badge-moderate';
          let statusLabel = 'Typical (P25 - P75)';

          if (bm.status === 'lower_than_typical') {
            statusBadgeClass = bm.risk_direction === 'high_is_bad' ? 'badge-favourable' : 'badge-caution';
            statusLabel = 'Lower Than Typical (< P25)';
          } else if (bm.status === 'higher_than_typical') {
            statusBadgeClass = bm.risk_direction === 'high_is_bad' ? 'badge-caution' : 'badge-favourable';
            statusLabel = 'Higher Than Typical (P75 - P95)';
          } else if (bm.status === 'very_high') {
            statusBadgeClass = 'badge-critical';
            statusLabel = 'Very High (> P95)';
          }

          return (
            <div
              key={bm.ingredient_key}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                padding: 'var(--space-sm)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-surface-container)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <div>
                  <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                    {bm.ingredient_key.replace('_', ' ')}
                  </span>
                  <span style={{ marginLeft: '8px', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                    <strong>{bm.amount_evaluated} {bm.unit}</strong>
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className={`badge ${statusBadgeClass}`}>
                    {isLimited ? 'Limited Data' : statusLabel}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
                    (n = {bm.sample_size.toLocaleString()})
                  </span>
                </div>
              </div>

              {isLimited ? (
                <div style={{ padding: 'var(--space-xs) 0', fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
                  ⚠️ Sample count ({bm.sample_size}) is below the PRD reliability threshold of 100 records. Percentiles not evaluated to prevent synthetic bias.
                </div>
              ) : (
                <div style={{ marginTop: 'var(--space-xs)' }}>
                  {/* Visual spectrum track */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 2fr 1fr 1fr',
                      height: '14px',
                      borderRadius: 'var(--radius-pill)',
                      overflow: 'hidden',
                      gap: '2px',
                    }}
                  >
                    <div
                      style={{
                        backgroundColor: bm.status === 'lower_than_typical' ? 'var(--color-accent)' : 'var(--color-border)',
                      }}
                      title="Lower (< P25)"
                    />
                    <div
                      style={{
                        backgroundColor: bm.status === 'typical' ? 'var(--color-accent)' : 'var(--color-border)',
                      }}
                      title="Typical (P25 - P75)"
                    />
                    <div
                      style={{
                        backgroundColor: bm.status === 'higher_than_typical' ? 'var(--color-accent)' : 'var(--color-border)',
                      }}
                      title="Higher (P75 - P95)"
                    />
                    <div
                      style={{
                        backgroundColor: bm.status === 'very_high' ? 'var(--color-accent)' : 'var(--color-border)',
                      }}
                      title="Very High (> P95)"
                    />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--color-text-subtle)', marginTop: '4px' }}>
                    <span>&lt; P25 (Lower)</span>
                    <span style={{ fontWeight: 600 }}>P25 - P75 (Typical Category Range)</span>
                    <span>P75 - P95</span>
                    <span>&gt; P95 (Very High)</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
