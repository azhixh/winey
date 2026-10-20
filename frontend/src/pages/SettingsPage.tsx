import React, { useState, useEffect } from 'react';
import {
  Settings,
  Sun,
  Moon,
  Laptop,
  Globe,
  Wine,
  Trash2,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';
import { getSettings, saveSettings, applyTheme } from '../services/settingsService';
import { clearHistory } from '../services/historyService';
import type { AppSettings } from '../types';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings>(getSettings());
  const [savedNotification, setSavedNotification] = useState<boolean>(false);
  const [clearedHistoryNotice, setClearedHistoryNotice] = useState<boolean>(false);
  const [clearedAllNotice, setClearedAllNotice] = useState<boolean>(false);

  useEffect(() => {
    setSettings(getSettings());
  }, []);

  const handleUpdate = (updates: Partial<AppSettings>) => {
    const updated = { ...settings, ...updates };
    setSettings(updated);
    saveSettings(updated);
    if (updates.theme) {
      applyTheme(updates.theme);
    }
    setSavedNotification(true);
    setTimeout(() => setSavedNotification(false), 2000);
  };

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to delete all saved beverage scan records?')) {
      clearHistory();
      setClearedHistoryNotice(true);
      setTimeout(() => setClearedHistoryNotice(false), 3000);
    }
  };

  const handleClearAllData = () => {
    if (
      window.confirm(
        'Are you sure you want to reset all preferences, settings, and scan records? This cannot be undone.'
      )
    ) {
      localStorage.clear();
      applyTheme('light');
      setSettings(getSettings());
      setClearedAllNotice(true);
      setTimeout(() => setClearedAllNotice(false), 3000);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)', maxWidth: '840px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Settings size={24} color="var(--color-accent)" />
            <h1>Application Settings</h1>
          </div>
          <p>
            Configure display themes, clinical regulatory baselines, and local-first storage.
          </p>
        </div>

        {savedNotification && (
          <span
            className="badge badge-favourable animate-fade-in"
            style={{ padding: '6px 12px', fontSize: '0.8125rem' }}
          >
            <CheckCircle2 size={14} /> Preferences Saved
          </span>
        )}
      </div>

      {/* 1. Theme Configuration */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <h3 style={{ marginBottom: 'var(--space-xs)' }}>Visual Theme</h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)', marginBottom: 'var(--space-md)' }}>
          Select your preferred interface appearance or sync with your operating system.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-md)' }}>
          {/* Light Theme */}
          <button
            type="button"
            onClick={() => handleUpdate({ theme: 'light' })}
            className="card"
            style={{
              padding: 'var(--space-md)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              cursor: 'pointer',
              border: settings.theme === 'light' ? '2px solid var(--color-accent)' : '1px solid var(--color-border)',
              backgroundColor: settings.theme === 'light' ? 'var(--color-accent-subtle)' : 'var(--color-surface)',
            }}
          >
            <Sun size={20} color={settings.theme === 'light' ? 'var(--color-accent)' : 'var(--color-text-muted)'} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Light Mode</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Luminescent clean</div>
            </div>
          </button>

          {/* Dark Theme */}
          <button
            type="button"
            onClick={() => handleUpdate({ theme: 'dark' })}
            className="card"
            style={{
              padding: 'var(--space-md)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              cursor: 'pointer',
              border: settings.theme === 'dark' ? '2px solid var(--color-accent)' : '1px solid var(--color-border)',
              backgroundColor: settings.theme === 'dark' ? 'var(--color-accent-subtle)' : 'var(--color-surface)',
            }}
          >
            <Moon size={20} color={settings.theme === 'dark' ? 'var(--color-accent)' : 'var(--color-text-muted)'} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Dark Mode</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>High-contrast dark</div>
            </div>
          </button>

          {/* System Theme */}
          <button
            type="button"
            onClick={() => handleUpdate({ theme: 'system' })}
            className="card"
            style={{
              padding: 'var(--space-md)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              cursor: 'pointer',
              border: settings.theme === 'system' ? '2px solid var(--color-accent)' : '1px solid var(--color-border)',
              backgroundColor: settings.theme === 'system' ? 'var(--color-accent-subtle)' : 'var(--color-surface)',
            }}
          >
            <Laptop size={20} color={settings.theme === 'system' ? 'var(--color-accent)' : 'var(--color-text-muted)'} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>System Sync</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-subtle)' }}>Follow OS setting</div>
            </div>
          </button>
        </div>
      </section>

      {/* 2. Regulatory & Standard Drink Settings */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <h3 style={{ marginBottom: 'var(--space-xs)' }}>Clinical & Regulatory Preferences</h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)', marginBottom: 'var(--space-md)' }}>
          Determine which jurisdictional guidelines and standard drink definitions are used for baseline analysis.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-lg)' }}>
          {/* Default Regulator Region */}
          <div className="form-group">
            <label className="form-label" htmlFor="setting-region">
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Globe size={16} /> Default Regulatory Region
              </span>
            </label>
            <select
              id="setting-region"
              className="form-input"
              value={settings.defaultRegion}
              onChange={(e) => handleUpdate({ defaultRegion: e.target.value })}
            >
              <option value="WHO">WHO / Codex Alimentarius (Global Standard)</option>
              <option value="EFSA">EFSA (European Food Safety Authority)</option>
              <option value="FDA">US FDA (Food and Drug Administration)</option>
              <option value="FSSAI">FSSAI (Food Safety Standards Authority of India)</option>
            </select>
            <span className="form-helper">Controls guideline limits and additive ADIs in new Lab scans</span>
          </div>

          {/* Standard Drink Definition */}
          <div className="form-group">
            <label className="form-label" htmlFor="setting-drink-def">
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Wine size={16} /> Standard Drink Definition (Pure Ethanol Mass)
              </span>
            </label>
            <select
              id="setting-drink-def"
              className="form-input"
              value={settings.standardDrinkDef}
              onChange={(e) => handleUpdate({ standardDrinkDef: parseFloat(e.target.value) || 10.0 })}
            >
              <option value="10">10.0 grams pure ethanol (WHO / International standard)</option>
              <option value="14">14.0 grams pure ethanol (US CDC / NIH standard drink)</option>
              <option value="8">8.0 grams pure ethanol (UK Unit)</option>
            </select>
            <span className="form-helper">Used to compute equivalent standard drinks from ABV and volume</span>
          </div>
        </div>
      </section>

      {/* 3. Storage & Privacy Controls */}
      <section className="card" style={{ padding: 'var(--space-xl)' }}>
        <h3 style={{ marginBottom: 'var(--space-xs)' }}>Storage & Privacy</h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-subtle)', marginBottom: 'var(--space-md)' }}>
          All scanned beverages and analytical inputs are stored locally in your browser. BQAS does not transmit personal health profiles to external servers.
        </p>

        {clearedHistoryNotice && (
          <div style={{ padding: '8px 12px', backgroundColor: 'var(--color-favourable-bg)', border: '1px solid var(--color-favourable-border)', borderRadius: 'var(--radius-sm)', color: 'var(--color-favourable-text)', fontSize: '0.8125rem', marginBottom: 'var(--space-md)' }}>
            ✓ Scan history has been cleared from local storage.
          </div>
        )}

        {clearedAllNotice && (
          <div style={{ padding: '8px 12px', backgroundColor: 'var(--color-favourable-bg)', border: '1px solid var(--color-favourable-border)', borderRadius: 'var(--radius-sm)', color: 'var(--color-favourable-text)', fontSize: '0.8125rem', marginBottom: 'var(--space-md)' }}>
            ✓ All local data and application settings have been reset.
          </div>
        )}

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
          <button
            onClick={handleClearHistory}
            className="btn btn-secondary"
            style={{ color: 'var(--color-critical-text)' }}
          >
            <Trash2 size={16} />
            <span>Clear Local Scan History</span>
          </button>

          <button
            onClick={handleClearAllData}
            className="btn btn-secondary"
            style={{ color: 'var(--color-critical-text)', borderColor: 'var(--color-critical-border)' }}
          >
            <RefreshCw size={16} />
            <span>Reset All Application Data</span>
          </button>
        </div>
      </section>
    </div>
  );
};
