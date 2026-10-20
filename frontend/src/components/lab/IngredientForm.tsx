import React, { useState } from 'react';
import type { BeverageCategory } from '../../types';
import { HelpCircle, AlertTriangle, Layers } from 'lucide-react';

interface IngredientFormProps {
  category: BeverageCategory;
  values: Record<string, any>;
  onChange: (field: string, value: any) => void;
  servingSizeMl: number;
  onServingSizeChange: (val: number) => void;
  productName: string;
  onProductNameChange: (val: string) => void;
  wineColor: 'red' | 'white';
  onWineColorChange: (color: 'red' | 'white') => void;
}

export const IngredientForm: React.FC<IngredientFormProps> = ({
  category,
  values,
  onChange,
  servingSizeMl,
  onServingSizeChange,
  productName,
  onProductNameChange,
  wineColor,
  onWineColorChange,
}) => {
  const [showAdvancedWine, setShowAdvancedWine] = useState(false);

  const handleNumericChange = (field: string, rawVal: string) => {
    if (rawVal.trim() === '') {
      onChange(field, null); // Preserve missing as null
      return;
    }
    const parsed = parseFloat(rawVal);
    if (!isNaN(parsed) && parsed >= 0) {
      onChange(field, parsed);
    }
  };

  const renderField = (
    key: string,
    label: string,
    unit: string,
    tooltip: string,
    placeholder = 'Leave blank if unknown',
    step = 'any',
    max?: number
  ) => {
    const rawVal = values[key];
    const displayVal = rawVal !== undefined && rawVal !== null ? rawVal : '';
    const hasPlausibilityWarning = max && typeof rawVal === 'number' && rawVal > max;

    return (
      <div className="form-group" key={key}>
        <div className="form-label">
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {label}
            <span style={{ color: 'var(--color-text-subtle)', fontWeight: 400 }}>({unit})</span>
            <span title={tooltip} style={{ cursor: 'help', color: 'var(--color-text-subtle)' }}>
              <HelpCircle size={14} />
            </span>
          </span>
        </div>

        <input
          type="number"
          min="0"
          step={step}
          className="form-input"
          placeholder={placeholder}
          value={displayVal}
          onChange={(e) => handleNumericChange(key, e.target.value)}
        />

        {hasPlausibilityWarning && (
          <span className="form-warning" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <AlertTriangle size={12} />
            Unusually high value (&gt; {max} {unit}). Please verify.
          </span>
        )}
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
      {/* Product Details Header Card */}
      <div className="card" style={{ padding: 'var(--space-lg)' }}>
        <h3 style={{ marginBottom: 'var(--space-md)' }}>General Details</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-md)' }}>
          {/* Product Name */}
          <div className="form-group">
            <label className="form-label" htmlFor="input-prod-name">
              Product / Sample Name (Optional)
            </label>
            <input
              id="input-prod-name"
              type="text"
              className="form-input"
              placeholder="e.g. Vintage Reserve, Classic Cola"
              value={productName}
              onChange={(e) => onProductNameChange(e.target.value)}
            />
            <span className="form-helper">Used to label your report and saved history</span>
          </div>

          {/* Serving Size */}
          <div className="form-group">
            <label className="form-label" htmlFor="input-serving">
              Serving Size (mL) <span style={{ color: 'var(--color-critical)' }}>*</span>
            </label>
            <input
              id="input-serving"
              type="number"
              min="10"
              max="5000"
              className="form-input"
              value={servingSizeMl || ''}
              onChange={(e) => onServingSizeChange(parseFloat(e.target.value) || 0)}
              required
            />
            <span className="form-helper">Required for alcohol mass and serving-based calculations</span>
          </div>
        </div>
      </div>

      {/* Category Specific Ingredient Inputs */}
      <div className="card" style={{ padding: 'var(--space-lg)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)' }}>
          <div>
            <h3>{category} Composition Inputs</h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
              Enter known laboratory, label, or analytical values. Blank inputs remain unassessed and are never converted to zero.
            </p>
          </div>

          {category === 'Wine' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--color-surface-dim)', padding: '4px', borderRadius: 'var(--radius-pill)' }}>
              <button
                type="button"
                onClick={() => onWineColorChange('red')}
                className={`btn ${wineColor === 'red' ? 'btn-primary' : 'btn-ghost'}`}
                style={{ padding: '4px 12px', fontSize: '0.8125rem', borderRadius: 'var(--radius-pill)' }}
              >
                Red Wine
              </button>
              <button
                type="button"
                onClick={() => onWineColorChange('white')}
                className={`btn ${wineColor === 'white' ? 'btn-primary' : 'btn-ghost'}`}
                style={{ padding: '4px 12px', fontSize: '0.8125rem', borderRadius: 'var(--radius-pill)' }}
              >
                White Wine
              </button>
            </div>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-md)' }}>
          {/* Soft Drinks */}
          {category === 'Soft drink' && (
            <>
              {renderField('sugars', 'Total Sugars', 'g', 'Free sugars per serving evaluated against WHO 25g/50g guidelines.', 'e.g. 35', '0.1', 100)}
              {renderField('calories', 'Energy', 'kcal', 'Total calorie content per serving.', 'e.g. 140', '1', 500)}
              {renderField('caffeine', 'Caffeine', 'mg', 'Caffeine content per serving evaluated against EFSA 200mg single-dose limit.', 'e.g. 32', '0.1', 300)}
              {renderField('sodium', 'Sodium', 'mg', 'Sodium content evaluated against WHO 2000mg/day guidance.', 'e.g. 20', '1', 1000)}
              {renderField('sodium_benzoate', 'Sodium Benzoate (E211)', 'mg/L', 'Preservative converted to benzoic acid equivalent using 0.848 factor.', 'e.g. 150', '1', 1000)}
              {renderField('pH', 'pH Level', 'pH', 'Measured acidity/alkalinity of beverage.', 'e.g. 2.5', '0.01', 14)}
              {renderField('phosphoric_acid', 'Phosphoric Acid', 'mg/L', 'Acidulant concentration in cola drinks.', 'e.g. 500', '1', 2000)}
            </>
          )}

          {/* Beer */}
          {category === 'Beer' && (
            <>
              {renderField('alcohol', 'Alcohol By Volume (ABV)', '%', 'Calculates pure ethanol mass and WHO standard drinks.', 'e.g. 5.0', '0.1', 25)}
              {renderField('calories', 'Energy', 'kcal', 'Total caloric density per serving.', 'e.g. 150', '1', 500)}
              {renderField('carbohydrates', 'Carbohydrates', 'g', 'Total carbohydrate load per serving.', 'e.g. 12.0', '0.1', 100)}
              {renderField('sulphites', 'Sulphites as SO2', 'mg/L', 'Preservative evaluated against EFSA 0.7 mg/kg ADI.', 'e.g. 10.0', '0.1', 200)}
              {renderField('bitterness', 'Bitterness (IBU)', 'IBU', 'International Bittering Units from hops.', 'e.g. 25', '1', 120)}
            </>
          )}

          {/* Energy Drinks */}
          {category === 'Energy drink' && (
            <>
              {renderField('caffeine', 'Caffeine', 'mg', 'Evaluated against EFSA acute single-dose (200mg) and daily limits.', 'e.g. 160', '0.1', 400)}
              {renderField('sugars', 'Total Sugars', 'g', 'Free sugars per serving evaluated against WHO guidelines.', 'e.g. 27', '0.1', 100)}
              {renderField('taurine', 'Taurine', 'mg', 'Information-only functional amino acid (EFSA 1000mg no-adverse threshold).', 'e.g. 1000', '1', 4000)}
              {renderField('sodium', 'Sodium', 'mg', 'Sodium mineral content per serving.', 'e.g. 180', '1', 1000)}
            </>
          )}

          {/* Spirits / Alcohol */}
          {category === 'Spirits' && (
            <>
              {renderField('alcohol', 'Alcohol By Volume (ABV)', '%', 'Volumetric alcohol strength.', 'e.g. 40.0', '0.1', 100)}
              {renderField('methanol', 'Methanol', 'g/L pure alcohol', 'Critical toxicological rule: breached if > 10.0 g/L pure alcohol.', 'e.g. 2.0', '0.01', 30)}
              {renderField('added_sugar', 'Added Sugar', 'g/L', 'Sugar added in liqueurs or flavored spirits.', 'e.g. 15.0', '0.1', 300)}
            </>
          )}

          {/* Wine Basic */}
          {category === 'Wine' && (
            <>
              {renderField('alcohol', 'Alcohol By Volume (% vol)', '%', 'Measured ethanol concentration.', 'e.g. 12.5', '0.1', 25)}
              {renderField('residual_sugar', 'Residual Sugar', 'g/L', 'Natural unfermented grape sugars.', 'e.g. 2.2', '0.1', 200)}
              {renderField('total_sulfur_dioxide', 'Total Sulfur Dioxide', 'mg/L', 'Total bound and free SO2 preservative.', 'e.g. 90', '1', 400)}
              {renderField('pH', 'pH Level', 'pH', 'Natural wine acidity balance.', 'e.g. 3.3', '0.01', 5)}
            </>
          )}
        </div>

        {/* Wine Advanced Section (for 11 UCI ML Features) */}
        {category === 'Wine' && (
          <div style={{ marginTop: 'var(--space-lg)', paddingTop: 'var(--space-md)', borderTop: '1px solid var(--color-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-sm)' }}>
              <div>
                <span style={{ fontWeight: 600, fontSize: '0.9375rem' }}>
                  Advanced Physicochemical Attributes (UCI Portuguese Vinho Verde ML Model)
                </span>
                <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
                  All 11 features are required to evaluate sensory quality estimation.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setShowAdvancedWine(!showAdvancedWine)}
                className="btn btn-secondary"
                style={{ padding: '4px 10px', fontSize: '0.8125rem' }}
              >
                <Layers size={14} />
                <span>{showAdvancedWine ? 'Hide Advanced' : 'Show 7 Advanced Attributes'}</span>
              </button>
            </div>

            {showAdvancedWine && (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: 'var(--space-md)',
                  marginTop: 'var(--space-md)',
                  padding: 'var(--space-md)',
                  backgroundColor: 'var(--color-surface-dim)',
                  borderRadius: 'var(--radius-md)',
                }}
              >
                {renderField('fixed_acidity', 'Fixed Acidity', 'g/L tartaric', 'Tartaric acid concentration.', 'e.g. 7.4', '0.1')}
                {renderField('volatile_acidity', 'Volatile Acidity', 'g/L acetic', 'Acetic acid volatile fraction.', 'e.g. 0.32', '0.01')}
                {renderField('citric_acid', 'Citric Acid', 'g/L', 'Citric acid freshness component.', 'e.g. 0.35', '0.01')}
                {renderField('chlorides', 'Chlorides', 'g/L NaCl', 'Sodium chloride salinity level.', 'e.g. 0.045', '0.001')}
                {renderField('free_sulfur_dioxide', 'Free Sulfur Dioxide', 'mg/L', 'Molecular and bisulfite free SO2.', 'e.g. 35', '1')}
                {renderField('density', 'Density', 'g/cm³', 'Liquid density at 20°C.', 'e.g. 0.9945', '0.0001')}
                {renderField('sulphates', 'Sulphates', 'g/L K2SO4', 'Potassium sulphate mineral additive.', 'e.g. 0.52', '0.01')}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
