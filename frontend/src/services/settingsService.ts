/**
 * BQAS User Preferences & Settings Service
 */

import type { AppSettings } from '../types';

const SETTINGS_KEY = 'bqas_settings_v1';

export const DEFAULT_SETTINGS: AppSettings = {
  theme: 'light',
  unitSystem: 'metric',
  defaultRegion: 'WHO',
  standardDrinkDef: 10.0,
  highContrast: false,
};

export function getSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch (e) {
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(settings: AppSettings): void {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    applyTheme(settings.theme);
  } catch (e) {
    console.error('Failed to save settings:', e);
  }
}

export function applyTheme(theme: 'light' | 'dark' | 'system'): void {
  const root = document.documentElement;
  let activeTheme: 'light' | 'dark' = 'light';

  if (theme === 'system') {
    activeTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  } else {
    activeTheme = theme;
  }

  root.setAttribute('data-theme', activeTheme);
}
