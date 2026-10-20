import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Coffee,
  Beer,
  Zap,
  Wine,
  Flame,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  Loader2,
  CheckCircle2,
  Search,
  Package,
  RotateCcw,
  Info,
} from 'lucide-react';
import { IngredientForm } from '../components/lab/IngredientForm';
import { PersonalizationPanel } from '../components/lab/PersonalizationPanel';
import {
  evaluateBeverage,
  searchProducts,
  getProductByBarcode,
  ApiError,
} from '../services/api';
import { saveHistoryItem } from '../services/historyService';
import { getSettings } from '../services/settingsService';
import type { BeverageCategory, UserProfile, ScoringEvaluationRequest } from '../types';

interface CategoryOption {
  id: BeverageCategory;
  name: string;
  desc: string;
  icon: React.ElementType;
  defaultServing: number;
}

const CATEGORIES: CategoryOption[] = [
  {
    id: 'Soft drink',
    name: 'Soft Drink',
    desc: 'Colas, lemon-lime sodas, tonic waters, and flavored sparkling drinks.',
    icon: Coffee,
    defaultServing: 355,
  },
  {
    id: 'Beer',
    name: 'Beer & Ales',
    desc: 'Lagers, ales, IPAs, stouts, pilsners, and craft beers.',
    icon: Beer,
    defaultServing: 330,
  },
  {
    id: 'Wine',
    name: 'Wine (Red & White)',
    desc: 'Red or white grape wines evaluated for residual sugar, SO2, and sensory quality.',
    icon: Wine,
    defaultServing: 150,
  },
  {
    id: 'Spirits',
    name: 'Alcohol / Spirits',
    desc: 'Distilled liquors (whiskey, gin, vodka, rum) evaluated for ABV and methanol.',
    icon: Flame,
    defaultServing: 44,
  },
  {
    id: 'Energy drink',
    name: 'Energy Drink',
    desc: 'Stimulant beverages formulated with caffeine, taurine, and B-vitamins.',
    icon: Zap,
    defaultServing: 250,
  },
];

export const LabPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const settings = getSettings();

  // Wizard Step: 1 = Category Select, 2 = Enter Details & Personalize
  const [step, setStep] = useState<1 | 2>(1);

  // Form State
  const [selectedCategory, setSelectedCategory] = useState<BeverageCategory>('Soft drink');
  const [productName, setProductName] = useState<string>('');
  const [servingSizeMl, setServingSizeMl] = useState<number>(355);
  const [wineColor, setWineColor] = useState<'red' | 'white'>('red');
  const [inputs, setInputs] = useState<Record<string, any>>({});

  // Product Lookup / Barcode Search State
  const [lookupQuery, setLookupQuery] = useState<string>('');
  const [lookupResults, setLookupResults] = useState<any[]>([]);
  const [isLookingUp, setIsLookingUp] = useState<boolean>(false);
  const [lookupMessage, setLookupMessage] = useState<string | null>(null);
  const [importedNotice, setImportedNotice] = useState<string | null>(null);

  // Personalization Panel State
  const [showPersonalization, setShowPersonalization] = useState<boolean>(false);
  const [userProfile, setUserProfile] = useState<UserProfile>({
    age_group: 'adult',
    weight_kg: 60,
    is_pregnant_or_breastfeeding: false,
    has_diabetes: false,
    has_heart_condition: false,
    regulator_region: settings.defaultRegion || 'WHO',
    standard_drink_definition_g: settings.standardDrinkDef || 10.0,
  });

  // Submission Status
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Preselect category from query param if available
  useEffect(() => {
    const catQuery = searchParams.get('category');
    if (catQuery) {
      const match = CATEGORIES.find(
        (c) =>
          c.id.toLowerCase() === catQuery.toLowerCase() ||
          c.name.toLowerCase() === catQuery.toLowerCase()
      );
      if (match) {
        setSelectedCategory(match.id);
        setServingSizeMl(match.defaultServing);
        setStep(2);
      }
    }
  }, [searchParams]);

  // Debounced product lookup
  useEffect(() => {
    const queryTrimmed = lookupQuery.trim();
    if (!queryTrimmed || queryTrimmed.length < 3) {
      setLookupResults([]);
      setLookupMessage(null);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLookingUp(true);
      setLookupMessage(null);

      // Check if query looks like a barcode (all digits, length 8-14)
      const isBarcode = /^\d{8,14}$/.test(queryTrimmed);

      try {
        if (isBarcode) {
          const product = await getProductByBarcode(queryTrimmed);
          if (product) {
            setLookupResults([product]);
          } else {
            setLookupResults([]);
            setLookupMessage(`No product found with barcode ${queryTrimmed}. Manual entry ready.`);
          }
        } else {
          // Text search
          const catFilter = ['Soft drink', 'Energy drink'].includes(selectedCategory)
            ? selectedCategory
            : undefined;
          const res = await searchProducts(queryTrimmed, catFilter);
          const products = res?.products || (Array.isArray(res) ? res : []);
          setLookupResults(products.slice(0, 5));
          if (products.length === 0) {
            setLookupMessage(`No products matching "${queryTrimmed}". Manual entry is always ready.`);
          }
        }
      } catch (err) {
        setLookupResults([]);
        setLookupMessage('External product catalog service is unreachable. Manual entry is ready below.');
      } finally {
        setIsLookingUp(false);
      }
    }, 450);

    return () => clearTimeout(timer);
  }, [lookupQuery, selectedCategory]);

  const handleSelectCategory = (cat: CategoryOption) => {
    setSelectedCategory(cat.id);
    setServingSizeMl(cat.defaultServing);
    setInputs({});
    setLookupQuery('');
    setLookupResults([]);
    setImportedNotice(null);
  };

  const handleResetForm = () => {
    setInputs({});
    setProductName('');
    const match = CATEGORIES.find((c) => c.id === selectedCategory);
    if (match) setServingSizeMl(match.defaultServing);
    setLookupQuery('');
    setLookupResults([]);
    setImportedNotice(null);
    setErrorMessage(null);
  };

  const handleImportProduct = (product: any) => {
    // Populate product name
    const name = product.product_name || product.name || '';
    if (name) setProductName(name);

    const nutrients = product.nutritional_values || product.nutrients || {};

    // Populate serving size if available and positive
    const sValue = nutrients.serving_size_value || product.serving_size_value;
    if (sValue && sValue > 0) {
      setServingSizeMl(parseFloat(sValue));
    }

    // Populate nutrients without imputing zero for missing fields
    const updatedInputs: Record<string, any> = { ...inputs };

    // Sugars (g)
    const sugarVal =
      nutrients.sugar_per_serving ??
      (nutrients.sugar_per_100ml !== null && nutrients.sugar_per_100ml !== undefined && servingSizeMl > 0
        ? (nutrients.sugar_per_100ml * servingSizeMl) / 100
        : null);
    if (sugarVal !== null && sugarVal !== undefined && !isNaN(sugarVal)) {
      updatedInputs['sugars'] = parseFloat(sugarVal.toFixed(1));
    }

    // Calories (kcal)
    const calVal =
      nutrients.calories_per_serving ??
      (nutrients.calories_per_100ml !== null && nutrients.calories_per_100ml !== undefined && servingSizeMl > 0
        ? (nutrients.calories_per_100ml * servingSizeMl) / 100
        : null);
    if (calVal !== null && calVal !== undefined && !isNaN(calVal)) {
      updatedInputs['calories'] = parseFloat(calVal.toFixed(0));
    }

    // Caffeine (mg)
    const caffVal =
      nutrients.caffeine_per_serving ??
      (nutrients.caffeine_per_100ml !== null && nutrients.caffeine_per_100ml !== undefined && servingSizeMl > 0
        ? (nutrients.caffeine_per_100ml * servingSizeMl) / 100
        : null);
    if (caffVal !== null && caffVal !== undefined && !isNaN(caffVal)) {
      updatedInputs['caffeine'] = parseFloat(caffVal.toFixed(1));
    }

    // Sodium (mg)
    const sodVal =
      nutrients.sodium_per_serving ??
      (nutrients.sodium_per_100ml !== null && nutrients.sodium_per_100ml !== undefined && servingSizeMl > 0
        ? (nutrients.sodium_per_100ml * servingSizeMl) / 100
        : null);
    if (sodVal !== null && sodVal !== undefined && !isNaN(sodVal)) {
      updatedInputs['sodium'] = parseFloat(sodVal.toFixed(1));
    }

    setInputs(updatedInputs);
    setLookupResults([]);
    setLookupQuery('');
    setImportedNotice(
      `Imported nutrition values for "${name || 'Product'}". From dataset, verify against physical package label.`
    );
  };

  const handleInputChange = (field: string, value: any) => {
    setInputs((prev) => {
      const next = { ...prev };
      if (value === null || value === undefined) {
        delete next[field];
      } else {
        next[field] = value;
      }
      return next;
    });
  };

  // Determine if submit is enabled
  const hasAtLeastOneIngredient = Object.keys(inputs).length > 0;
  const isServingValid = servingSizeMl > 0 && !isNaN(servingSizeMl);
  const canSubmit = hasAtLeastOneIngredient && isServingValid && !isLoading;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setIsLoading(true);
    setErrorMessage(null);

    const payload: ScoringEvaluationRequest = {
      beverage_type: selectedCategory,
      serving_size_ml: servingSizeMl,
      product_name: productName.trim() || undefined,
      wine_color: selectedCategory === 'Wine' ? wineColor : undefined,
      inputs,
      profile: showPersonalization ? userProfile : undefined,
    };

    try {
      const result = await evaluateBeverage(payload);
      // Persist to local guest history with raw inputs
      const savedRecord = saveHistoryItem(result, productName.trim() || undefined, inputs);
      // Navigate to results screen
      navigate(`/result?id=${savedRecord.id}`, { state: { result } });
    } catch (err: any) {
      console.error('Analysis failed:', err);
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(
          'Failed to communicate with analysis server. Please ensure the backend is running.'
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      {/* Wizard Step Progress Indicator */}
      <div
        className="glass-panel"
        style={{
          padding: 'var(--space-md) var(--space-lg)',
          borderRadius: 'var(--radius-lg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              backgroundColor: step === 1 ? 'var(--color-accent)' : 'var(--color-favourable)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.8125rem',
            }}
          >
            {step > 1 ? <CheckCircle2 size={16} /> : '1'}
          </div>
          <div>
            <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>Step 1: Category Selection</span>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
              {selectedCategory} selected
            </p>
          </div>
        </div>

        <div style={{ width: '40px', height: '2px', backgroundColor: 'var(--color-border)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              backgroundColor: step === 2 ? 'var(--color-accent)' : 'var(--color-surface-dim)',
              color: step === 2 ? '#fff' : 'var(--color-text-subtle)',
              border: step === 2 ? 'none' : '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.8125rem',
            }}
          >
            2
          </div>
          <div>
            <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>Step 2: Composition & Personalization</span>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
              Analytical inputs & guidelines
            </p>
          </div>
        </div>
      </div>

      {/* Step 1: Beverage Selection Grid */}
      {step === 1 && (
        <section className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          <div>
            <h2>Select Beverage Category</h2>
            <p>
              Each category has tailored clinical guideline models, specific unit normalizations, and empirical benchmark sets.
            </p>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
              gap: 'var(--space-md)',
            }}
          >
            {CATEGORIES.map((cat) => {
              const isSelected = selectedCategory === cat.id;
              const Icon = cat.icon;
              return (
                <div
                  key={cat.id}
                  onClick={() => handleSelectCategory(cat)}
                  className="card"
                  style={{
                    padding: 'var(--space-lg)',
                    cursor: 'pointer',
                    borderColor: isSelected ? 'var(--color-accent)' : 'var(--color-border)',
                    boxShadow: isSelected ? '0 0 0 2px var(--color-accent)' : 'var(--shadow-sm)',
                    backgroundColor: isSelected ? 'var(--color-accent-subtle)' : 'var(--color-surface)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: 'var(--space-md)',
                    transition: 'all var(--transition-fast)',
                  }}
                  role="button"
                  tabIndex={0}
                  aria-pressed={isSelected}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') handleSelectCategory(cat);
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <div
                      style={{
                        width: '44px',
                        height: '44px',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'var(--color-surface)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: isSelected ? 'var(--color-accent)' : 'var(--color-primary)',
                        border: '1px solid var(--color-border)',
                      }}
                    >
                      <Icon size={24} />
                    </div>
                    {isSelected && (
                      <span className="badge badge-favourable">Selected</span>
                    )}
                  </div>

                  <div>
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '4px' }}>{cat.name}</h3>
                    <p style={{ fontSize: '0.875rem' }}>{cat.desc}</p>
                  </div>

                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)', borderTop: '1px solid var(--color-border)', paddingTop: '8px' }}>
                    Standard serving reference: <strong>{cat.defaultServing} mL</strong>
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-md)' }}>
            <button
              onClick={() => setStep(2)}
              className="btn btn-primary"
              style={{ padding: '0.75rem 2rem', fontSize: '1rem' }}
            >
              <span>Continue to Inputs</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </section>
      )}

      {/* Step 2: Beverage Details, Ingredients & Personalization Form */}
      {step === 2 && (
        <form onSubmit={handleSubmit} className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          {/* Top Bar with Back, Reset, and Category Badge */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="btn btn-secondary"
                style={{ padding: '6px 14px' }}
              >
                <ArrowLeft size={16} />
                <span>Back to Category</span>
              </button>

              <button
                type="button"
                onClick={handleResetForm}
                className="btn btn-ghost"
                style={{ padding: '6px 12px', fontSize: '0.8125rem' }}
                title="Clear all fields to start fresh"
              >
                <RotateCcw size={14} />
                <span>Reset Form</span>
              </button>
            </div>

            <span className="badge badge-neutral" style={{ padding: '6px 12px', fontSize: '0.875rem' }}>
              Category: <strong>{selectedCategory}</strong>
            </span>
          </div>

          {/* Optional Product / Barcode Search Importer */}
          {['Soft drink', 'Energy drink'].includes(selectedCategory) && (
            <div
              className="card"
              style={{
                padding: 'var(--space-md) var(--space-lg)',
                backgroundColor: 'var(--color-surface-dim)',
                border: '1px dashed var(--color-border-strong)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Package size={18} color="var(--color-accent)" />
                <span style={{ fontWeight: 600, fontSize: '0.9375rem' }}>
                  Quick Lookup: Import from Open Food Facts or Barcode (Optional)
                </span>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-subtle)', marginBottom: 'var(--space-sm)' }}>
                Type a brand name (e.g. "Coca Cola", "Red Bull") or an 8–14 digit barcode. Manual entry is always ready below.
              </p>

              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Search size={18} color="var(--color-text-subtle)" style={{ position: 'absolute', left: '12px', pointerEvents: 'none' }} />
                <input
                  type="text"
                  className="form-input"
                  style={{ paddingLeft: '38px', fontSize: '0.875rem' }}
                  placeholder="Enter product title or numerical barcode..."
                  value={lookupQuery}
                  onChange={(e) => setLookupQuery(e.target.value)}
                />
                {isLookingUp && (
                  <Loader2 size={16} className="animate-spin" style={{ position: 'absolute', right: '12px', color: 'var(--color-text-subtle)' }} />
                )}
              </div>

              {lookupMessage && (
                <div style={{ marginTop: '8px', fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                  {lookupMessage}
                </div>
              )}

              {lookupResults.length > 0 && (
                <div style={{ marginTop: 'var(--space-sm)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {lookupResults.map((prod, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--color-surface)',
                        border: '1px solid var(--color-border)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div>
                        <strong>{prod.product_name || prod.name || 'Unnamed Product'}</strong>
                        <span style={{ marginLeft: '8px', fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>
                          {prod.brands || prod.brand || ''}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleImportProduct(prod)}
                        className="btn btn-primary"
                        style={{ padding: '4px 12px', fontSize: '0.8125rem' }}
                      >
                        Import Values
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Imported Data Notice */}
          {importedNotice && (
            <div
              className="card animate-fade-in"
              style={{
                padding: 'var(--space-sm) var(--space-md)',
                backgroundColor: 'var(--color-surface-container)',
                borderLeft: '4px solid var(--color-accent)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.875rem',
              }}
            >
              <Info size={18} color="var(--color-accent)" />
              <div>
                <strong>From dataset, verify against label:</strong> {importedNotice}
              </div>
            </div>
          )}

          {/* Error Message Alert */}
          {errorMessage && (
            <div
              className="card"
              style={{
                padding: 'var(--space-md)',
                backgroundColor: 'var(--color-critical-bg)',
                borderColor: 'var(--color-critical-border)',
                color: 'var(--color-critical-text)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-sm)',
              }}
            >
              <AlertCircle size={20} />
              <div style={{ flex: 1, fontSize: '0.875rem' }}>{errorMessage}</div>
            </div>
          )}

          {/* Form Component */}
          <IngredientForm
            category={selectedCategory}
            values={inputs}
            onChange={handleInputChange}
            servingSizeMl={servingSizeMl}
            onServingSizeChange={setServingSizeMl}
            productName={productName}
            onProductNameChange={setProductName}
            wineColor={wineColor}
            onWineColorChange={setWineColor}
          />

          {/* Optional Personalization Panel */}
          <PersonalizationPanel
            profile={userProfile}
            onChange={setUserProfile}
            isOpen={showPersonalization}
            onToggle={() => setShowPersonalization(!showPersonalization)}
          />

          {/* Submission Area */}
          <div
            className="card"
            style={{
              padding: 'var(--space-lg)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-md)',
              backgroundColor: 'var(--color-surface-container)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
              <div>
                <span style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Ready for Evaluation?</span>
                <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-subtle)' }}>
                  {hasAtLeastOneIngredient
                    ? `${Object.keys(inputs).length} analytical parameter(s) supplied. Missing fields remain non-zero unassessed.`
                    : 'Please enter at least one numeric ingredient parameter above.'}
                </p>
              </div>

              <button
                type="submit"
                disabled={!canSubmit}
                className="btn btn-primary"
                style={{
                  padding: '0.875rem 2rem',
                  fontSize: '1rem',
                  opacity: canSubmit ? 1 : 0.6,
                  cursor: canSubmit ? 'pointer' : 'not-allowed',
                }}
              >
                {isLoading ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    <span>Evaluating via PRD Engine...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    <span>Analyze Beverage</span>
                    <ArrowRight size={18} />
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
};
