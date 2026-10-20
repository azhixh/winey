import React from 'react';
import type { UserProfile } from '../../types';
import { UserCheck, ShieldAlert, ChevronDown, ChevronUp } from 'lucide-react';

interface PersonalizationPanelProps {
  profile: UserProfile;
  onChange: (updated: UserProfile) => void;
  isOpen: boolean;
  onToggle: () => void;
}

export const PersonalizationPanel: React.FC<PersonalizationPanelProps> = ({
  profile,
  onChange,
  isOpen,
  onToggle,
}) => {
  return (
    <div
      className="card"
      style={{
        marginTop: 'var(--space-md)',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        border: '1px solid var(--color-border)',
      }}
    >
      <button
        type="button"
        onClick={onToggle}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: 'var(--space-md) var(--space-lg)',
          backgroundColor: 'var(--color-surface-dim)',
          fontWeight: 600,
          color: 'var(--color-text-main)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <UserCheck size={18} color="var(--color-accent)" />
          <span>Personalize Analysis (Optional)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
            {isOpen ? 'Collapse' : 'Expand (Minors, Pregnancy, Body Weight)'}
          </span>
          {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {isOpen && (
        <div style={{ padding: 'var(--space-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            Personalization scales caffeine single-dose/daily limits, sodium benzoate ADI (5 mg/kg), and sulphite ADI (0.7 mg/kg) according to European Food Safety Authority (EFSA) and WHO guidelines.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-md)' }}>
            {/* Age Group */}
            <div className="form-group">
              <label className="form-label" htmlFor="pref-age-group">
                Age Group
              </label>
              <select
                id="pref-age-group"
                className="form-input"
                value={profile.age_group}
                onChange={(e) =>
                  onChange({ ...profile, age_group: e.target.value as 'adult' | 'under_18' })
                }
              >
                <option value="adult">Adult (18+)</option>
                <option value="under_18">Under 18 (Strict 3 mg/kg caffeine limit)</option>
              </select>
            </div>

            {/* Body Weight */}
            <div className="form-group">
              <label className="form-label" htmlFor="pref-weight">
                Body Weight (kg)
              </label>
              <input
                id="pref-weight"
                type="number"
                min="20"
                max="300"
                step="1"
                className="form-input"
                value={profile.weight_kg}
                onChange={(e) =>
                  onChange({ ...profile, weight_kg: parseFloat(e.target.value) || 60 })
                }
              />
              <span className="form-helper">Used for mg/kg body-weight ADI scaling</span>
            </div>

            {/* Regulatory Region */}
            <div className="form-group">
              <label className="form-label" htmlFor="pref-region">
                Regulatory Baseline
              </label>
              <select
                id="pref-region"
                className="form-input"
                value={profile.regulator_region}
                onChange={(e) =>
                  onChange({ ...profile, regulator_region: e.target.value })
                }
              >
                <option value="WHO">WHO / Codex Alimentarius</option>
                <option value="EFSA">EFSA (European Union)</option>
                <option value="FDA">US FDA</option>
                <option value="FSSAI">FSSAI (India)</option>
              </select>
            </div>

            {/* Standard Drink Definition */}
            <div className="form-group">
              <label className="form-label" htmlFor="pref-std-drink">
                Standard Drink Definition
              </label>
              <select
                id="pref-std-drink"
                className="form-input"
                value={profile.standard_drink_definition_g}
                onChange={(e) =>
                  onChange({
                    ...profile,
                    standard_drink_definition_g: parseFloat(e.target.value) || 10,
                  })
                }
              >
                <option value="10">10.0 g (WHO Standard)</option>
                <option value="14">14.0 g (US CDC / NIH)</option>
                <option value="8">8.0 g (UK Unit)</option>
              </select>
            </div>
          </div>

          {/* Pregnancy Checkbox */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              id="pref-pregnant"
              type="checkbox"
              checked={profile.is_pregnant_or_breastfeeding}
              onChange={(e) =>
                onChange({ ...profile, is_pregnant_or_breastfeeding: e.target.checked })
              }
              style={{ width: '18px', height: '18px', accentColor: 'var(--color-accent)' }}
            />
            <label htmlFor="pref-pregnant" style={{ fontSize: '0.875rem', fontWeight: 500, cursor: 'pointer' }}>
              Pregnant or Breastfeeding (Triggers 200 mg/day caffeine cap and alcohol contraindication)
            </label>
          </div>

          {/* Condition Warning Message */}
          {(profile.is_pregnant_or_breastfeeding || profile.age_group === 'under_18') && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: 'var(--space-sm) var(--space-md)',
                backgroundColor: 'var(--color-caution-bg)',
                border: '1px solid var(--color-caution-border)',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.8125rem',
                color: 'var(--color-caution-text)',
              }}
            >
              <ShieldAlert size={18} />
              <span>
                Health Alert: Stricter toxicological limits will apply for minors / pregnancy. Alcohol reports will display mandatory contraindication warnings.
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
