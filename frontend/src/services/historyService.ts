/**
 * Local-First Guest History Service
 * Persists evaluated beverage reports safely in LocalStorage.
 * Handles malformed, corrupted, or outdated stored records safely.
 */

import type { HistoryRecord, ScoringEngineResult } from '../types';

const STORAGE_KEY = 'bqas_history_v1';

export function getHistory(): HistoryRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];

    // Filter and sanitize items to prevent crashing from malformed records
    return parsed.filter((item): item is HistoryRecord => {
      return (
        item &&
        typeof item === 'object' &&
        typeof item.id === 'string' &&
        typeof item.beverage_type === 'string' &&
        item.result &&
        typeof item.result === 'object'
      );
    });
  } catch (e) {
    console.error('Failed to load history from LocalStorage:', e);
    return [];
  }
}

export function getHistoryItem(id: string): HistoryRecord | undefined {
  const items = getHistory();
  return items.find((item) => item.id === id);
}

export function saveHistoryItem(
  result: ScoringEngineResult,
  customName?: string,
  inputs?: Record<string, any>
): HistoryRecord {
  const items = getHistory();
  const id = `scan_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
  const record: HistoryRecord = {
    id,
    timestamp: new Date().toISOString(),
    product_name: customName || result.product_name || `${result.beverage_type} Sample`,
    beverage_type: result.beverage_type,
    serving_size_ml: result.serving_size_ml,
    health_impact_score: result.health_impact_score,
    composition_score: result.composition_score,
    confidence_level: result.confidence_level,
    is_critical: result.critical_override?.is_critical || false,
    rules_version: result.rules_version,
    dataset_version: result.dataset_version,
    inputs: inputs || {},
    result,
  };

  const updated = [record, ...items].slice(0, 50); // Keep last 50
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (e) {
    console.error('Failed to save record to LocalStorage:', e);
  }

  return record;
}

export function deleteHistoryItem(id: string): void {
  const items = getHistory();
  const filtered = items.filter((item) => item.id !== id);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  } catch (e) {
    console.error('Failed to delete history item:', e);
  }
}

export function clearHistory(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    console.error('Failed to clear history:', e);
  }
}
