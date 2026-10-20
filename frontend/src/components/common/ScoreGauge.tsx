import React from 'react';

interface ScoreGaugeProps {
  score?: number | null;
  uncappedScore?: number | null;
  title: string;
  subtitle: string;
  type: 'health' | 'composition';
  isCritical?: boolean;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({
  score,
  uncappedScore,
  title,
  subtitle,
  type,
  isCritical,
}) => {
  const hasScore = score !== undefined && score !== null && !isNaN(score);
  const validScore = hasScore ? Math.max(0, Math.min(100, score as number)) : 0;

  // Circle dimensions
  const radius = 64;
  const strokeWidth = 10;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = hasScore
    ? circumference - (validScore / 100) * circumference
    : circumference;

  // Determine color and band
  let color = 'var(--color-moderate)';
  let band = 'Moderate';
  let badgeClass = 'badge-moderate';

  if (!hasScore) {
    band = 'Not Evaluated';
    badgeClass = 'badge-neutral';
    color = 'var(--color-border-strong)';
  } else if (isCritical) {
    color = 'var(--color-critical)';
    band = 'Critical Limit Capped';
    badgeClass = 'badge-critical';
  } else if (validScore >= 80) {
    color = 'var(--color-favourable)';
    band = 'Favourable';
    badgeClass = 'badge-favourable';
  } else if (validScore >= 60) {
    color = 'var(--color-moderate)';
    band = 'Moderate';
    badgeClass = 'badge-moderate';
  } else if (validScore >= 20) {
    color = 'var(--color-caution)';
    band = 'Caution';
    badgeClass = 'badge-caution';
  } else {
    color = 'var(--color-critical)';
    band = 'High Concern';
    badgeClass = 'badge-critical';
  }

  return (
    <div
      className="card"
      style={{
        padding: 'var(--space-lg)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        position: 'relative',
        flex: 1,
        minWidth: '260px',
      }}
      role="region"
      data-score-type={type}
      aria-label={`${title}: ${hasScore ? validScore : 'Not evaluated'}`}
    >
      <div style={{ marginBottom: 'var(--space-sm)' }}>
        <h3 style={{ fontSize: '1.125rem', marginBottom: '2px' }}>{title}</h3>
        <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
          {subtitle}
        </p>
      </div>

      <div style={{ position: 'relative', width: '160px', height: '160px', margin: 'var(--space-xs) 0' }}>
        <svg
          width="160"
          height="160"
          viewBox="0 0 160 160"
          style={{ transform: 'rotate(-90deg)', overflow: 'visible' }}
        >
          {/* Background circle track */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            fill="transparent"
            stroke="var(--color-surface-dim)"
            strokeWidth={strokeWidth}
          />
          {/* Active progress track */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            fill="transparent"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 800ms cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          />
        </svg>

        {/* Center score readout */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '2.5rem',
              fontWeight: 800,
              color: 'var(--color-text-main)',
              lineHeight: 1,
            }}
          >
            {hasScore ? validScore.toFixed(0) : '—'}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)', marginTop: '2px' }}>
            / 100
          </span>
        </div>
      </div>

      <div style={{ marginTop: 'var(--space-xs)' }}>
        <span className={`badge ${badgeClass}`}>{band}</span>
      </div>

      {isCritical && uncappedScore !== null && uncappedScore !== undefined && (
        <p
          style={{
            fontSize: '0.75rem',
            color: 'var(--color-critical-text)',
            marginTop: 'var(--space-xs)',
          }}
        >
          Capped at 40 (Underlying raw score: {uncappedScore.toFixed(0)})
        </p>
      )}
    </div>
  );
};
