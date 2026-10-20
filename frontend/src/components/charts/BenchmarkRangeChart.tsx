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
    <div className="card" style={{ padding: 'var(--space-lg)' }} role="region" aria-label="Category Benchmark Comparison Chart">
      <div style={{ marginBottom: 'var(--space-md)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <h3>Empirical Category Benchmark Distributions</h3>
          <span className="badge badge-neutral" style={{ fontSize: '0.75rem' }}>
            Empirical Threshold: n ≥ 100 Verified Records
          </span>
        </div>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)' }}>
          Comparing normalized nutrient density per 100 mL against verified public records for {categoryName}.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
        {benchmarks.map((bm) => {
          const isLimited = !bm.is_sufficient || bm.status === 'limited_benchmark_data';

          let statusBadgeClass = 'badge-moderate';
          let statusLabel = 'Typical (P25 - P75)';
          let statusTextSummary = 'Within the interquartile typical range.';

          if (bm.status === 'lower_than_typical') {
            statusBadgeClass = bm.risk_direction === 'high_is_bad' ? 'badge-favourable' : 'badge-caution';
            statusLabel = 'Lower Than Typical (< P25)';
            statusTextSummary = 'Below the 25th percentile of the category.';
          } else if (bm.status === 'higher_than_typical') {
            statusBadgeClass = bm.risk_direction === 'high_is_bad' ? 'badge-caution' : 'badge-favourable';
            statusLabel = 'Higher Than Typical (P75 - P95)';
            statusTextSummary = 'Above the 75th percentile of the category.';
          } else if (bm.status === 'very_high') {
            statusBadgeClass = 'badge-critical';
            statusLabel = 'Very High (> P95)';
            statusTextSummary = 'Above the 95th percentile (extreme high outlier).';
          }

          const ingredientDisplay = bm.ingredient_key.replace(/_/g, ' ');

          return (
            <div
              key={bm.ingredient_key}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                padding: 'var(--space-md)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-surface-container)',
                border: '1px solid var(--color-border)',
              }}
              role="group"
              aria-label={`${ingredientDisplay}: ${bm.amount_evaluated} ${bm.unit}, ${statusLabel}`}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <div>
                  <span style={{ fontWeight: 600, textTransform: 'capitalize', fontSize: '1rem' }}>
                    {ingredientDisplay}
                  </span>
                  <span style={{ marginLeft: '8px', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                    Measured: <strong>{bm.amount_evaluated} {bm.unit}</strong>
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className={`badge ${statusBadgeClass}`}>
                    {isLimited ? 'Limited Data' : statusLabel}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
                    (n = {bm.sample_size?.toLocaleString() || 0})
                  </span>
                </div>
              </div>

              {isLimited ? (
                <div style={{ padding: 'var(--space-xs) 0', fontSize: '0.8125rem', color: 'var(--color-caution-text)' }}>
                  ⚠️ Sample count ({bm.sample_size}) is below the PRD reliability threshold of 100 records. Percentiles not evaluated to prevent synthetic bias.
                </div>
              ) : (
                <div style={{ marginTop: 'var(--space-2xs)' }}>
                  {/* Visual spectrum track */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 2fr 1fr 1fr',
                      height: '16px',
                      borderRadius: 'var(--radius-pill)',
                      overflow: 'hidden',
                      gap: '3px',
                      backgroundColor: 'var(--color-surface-dim)',
                      padding: '2px',
                    }}
                    role="img"
                    aria-label={`Quartile range chart for ${ingredientDisplay}`}
                  >
                    <div
                      style={{
                        backgroundColor: bm.status === 'lower_than_typical' ? 'var(--color-accent)' : 'var(--color-border)',
                        borderRadius: 'var(--radius-pill) 0 0 var(--radius-pill)',
                        transition: 'background-color var(--transition-normal)',
                      }}
                      title="Lower (< P25)"
                    />
                    <div
                      style={{
                        backgroundColor: bm.status === 'typical' ? 'var(--color-accent)' : 'var(--color-border)',
                        transition: 'background-color var(--transition-normal)',
                      }}
                      title="Typical (P25 - P75)"
                    />
                    <div
                      style={{
                        backgroundColor: bm.status === 'higher_than_typical' ? 'var(--color-accent)' : 'var(--color-border)',
                        transition: 'background-color var(--transition-normal)',
                      }}
                      title="Higher (P75 - P95)"
                    />
                    <div
                      style={{
                        backgroundColor: bm.status === 'very_high' ? 'var(--color-accent)' : 'var(--color-border)',
                        borderRadius: '0 var(--radius-pill) var(--radius-pill) 0',
                        transition: 'background-color var(--transition-normal)',
                      }}
                      title="Very High (> P95)"
                    />
                  </div>

                  {/* Accessible legend and quartile boundaries */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.725rem', color: 'var(--color-text-subtle)', marginTop: '6px' }}>
                    <span>&lt; P25 (Lower)</span>
                    <span style={{ fontWeight: 600 }}>P25 – P75 (Typical Category Band)</span>
                    <span>P75 – P95 (Elevated)</span>
                    <span>&gt; P95 (Extreme)</span>
                  </div>

                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                    Status: {statusTextSummary} Credit: {bm.credit !== null && bm.credit !== undefined ? `${bm.credit} pts` : 'Reference only'}.
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
