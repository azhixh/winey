import React from 'react';
import type { IngredientSubscore } from '../../types';

interface GuidelineChartProps {
  evaluations: IngredientSubscore[];
}

export const GuidelineChart: React.FC<GuidelineChartProps> = ({ evaluations }) => {
  if (!evaluations || evaluations.length === 0) {
    return (
      <div className="card" style={{ padding: 'var(--space-lg)', textAlign: 'center' }}>
        <p style={{ color: 'var(--color-text-subtle)' }}>No guideline limits available for evaluation.</p>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: 'var(--space-lg)' }}>
      <div style={{ marginBottom: 'var(--space-md)' }}>
        <h3>Guideline Limit Comparison</h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)' }}>
          Normalized amount per serving compared against authoritative daily/single limits.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
        {evaluations.map((item) => {
          const ratio = item.guideline_ratio;
          const pct = Math.min(100, (ratio / 3.0) * 100); // 3.0 ratio = 100% of chart bar
          const limitMarkerPct = (1.0 / 3.0) * 100; // 1.0 limit = 33.3%

          let barColor = 'var(--color-favourable)';
          if (item.is_critical_breach) barColor = 'var(--color-critical)';
          else if (ratio > 2.0) barColor = 'var(--color-critical)';
          else if (ratio > 1.0) barColor = 'var(--color-caution)';
          else if (ratio > 0.5) barColor = 'var(--color-moderate)';

          return (
            <div key={item.ingredient_key} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                <span style={{ fontWeight: 600 }}>{item.ingredient_name}</span>
                <span style={{ color: 'var(--color-text-muted)' }}>
                  <strong>{item.amount_per_serving} {item.unit}</strong> (Limit: {item.guideline_limit} {item.unit})
                </span>
              </div>

              {/* Progress bar container */}
              <div
                style={{
                  position: 'relative',
                  height: '24px',
                  backgroundColor: 'var(--color-surface-dim)',
                  borderRadius: 'var(--radius-sm)',
                  overflow: 'hidden',
                }}
              >
                {/* 100% threshold guide line */}
                <div
                  style={{
                    position: 'absolute',
                    left: `${limitMarkerPct}%`,
                    top: 0,
                    bottom: 0,
                    width: '2px',
                    backgroundColor: 'var(--color-text-subtle)',
                    zIndex: 2,
                    opacity: 0.6,
                  }}
                  title="Guideline Limit (100%)"
                />

                {/* Filled portion */}
                <div
                  style={{
                    width: `${Math.max(4, pct)}%`,
                    height: '100%',
                    backgroundColor: barColor,
                    borderRadius: 'var(--radius-sm)',
                    transition: 'width 600ms cubic-bezier(0.16, 1, 0.3, 1)',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
                <span>0%</span>
                <span style={{ transform: 'translateX(50%)' }}>100% Limit</span>
                <span>300%+ High</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
