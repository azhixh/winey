/**
 * BQAS API Client & Integration Service
 * Connects directly to FastAPI backend and PRD Section 12 Scoring Engine.
 * Features:
 * - Environment-configured base URL (VITE_API_BASE_URL)
 * - 10-second request timeout controller to avoid infinite hangs
 * - Typed request/response contracts for scoring, references, product lookup, and ML
 * - Graceful error handling distinguishing network failures, timeouts, and validation errors
 */

import type {
  ScoringEvaluationRequest,
  ScoringEngineResult,
  RulesData,
  ReferenceRangesData,
  WineModelResult,
} from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const DEFAULT_TIMEOUT_MS = 10000;

export class ApiError extends Error {
  status: number;
  data: any;
  constructor(message: string, status: number, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      ...options,
      signal: options.signal || controller.signal,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errBody;
      try {
        errBody = await response.json();
      } catch {
        errBody = await response.text();
      }
      throw new ApiError(
        errBody?.message || errBody?.detail || `API error ${response.status}`,
        response.status,
        errBody
      );
    }

    return await response.json();
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) throw err;
    if (err.name === 'AbortError') {
      throw new ApiError(`Request to ${endpoint} timed out after ${DEFAULT_TIMEOUT_MS / 1000}s.`, 408);
    }
    throw new ApiError(err?.message || 'Network communication failure. Please check backend status.', 0);
  }
}

/**
 * Run deterministic PRD Section 12 scoring pipeline
 */
export async function evaluateBeverage(
  payload: ScoringEvaluationRequest
): Promise<ScoringEngineResult> {
  return request<ScoringEngineResult>('/api/scoring/evaluate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Fetch centralized rules configuration
 */
export async function getScoringRules(): Promise<RulesData> {
  return request<RulesData>('/api/scoring/rules');
}

/**
 * Fetch reference benchmark distributions
 */
export async function getScoringBenchmarks(): Promise<ReferenceRangesData> {
  return request<ReferenceRangesData>('/api/scoring/benchmarks');
}

/**
 * Fetch category-specific reference benchmarks and sample sizes
 * GET /api/reference/{category}
 */
export async function getCategoryReference(category: string): Promise<any> {
  return request<any>(`/api/reference/${encodeURIComponent(category)}`);
}

/**
 * Search external products (Open Food Facts / USDA FoodData)
 * GET /api/product-search?q=...
 */
export async function searchProducts(
  query: string,
  beverageType?: string
): Promise<any> {
  const params = new URLSearchParams({ q: query });
  if (beverageType) params.append('beverage_type', beverageType);
  return request(`/api/product-search?${params.toString()}`);
}

/**
 * Lookup product directly by barcode
 * GET /api/product/{barcode}
 */
export async function getProductByBarcode(barcode: string): Promise<any> {
  const cleanBarcode = barcode.trim();
  return request<any>(`/api/product/${encodeURIComponent(cleanBarcode)}`);
}

/**
 * Predict wine sensory quality rating via UCI ML model
 * POST /api/wine/predict
 */
export async function predictWineQuality(
  wineType: 'red' | 'white',
  features: Record<string, number>
): Promise<WineModelResult> {
  return request<WineModelResult>('/api/wine/predict', {
    method: 'POST',
    body: JSON.stringify({ wine_type: wineType, ...features }),
  });
}

/**
 * Check backend health status
 * GET /api/health
 */
export async function checkBackendHealth(): Promise<{ status: string; version: string }> {
  return request<{ status: string; version: string }>('/api/health');
}
