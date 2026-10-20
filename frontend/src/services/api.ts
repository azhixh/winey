/**
 * BQAS API Client & Integration Service
 * Connects directly to FastAPI backend and PRD Section 12 Scoring Engine.
 */

import type {
  ScoringEvaluationRequest,
  ScoringEngineResult,
  RulesData,
  ReferenceRangesData,
  WineModelResult,
} from '../types';

const API_BASE_URL = '';

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

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

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
    if (err instanceof ApiError) throw err;
    throw new ApiError(err?.message || 'Network communication failure', 0);
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
 * Search external products (Open Food Facts / USDA FoodData)
 */
export async function searchProducts(
  query: string,
  beverageType?: string
): Promise<any> {
  const params = new URLSearchParams({ q: query });
  if (beverageType) params.append('beverage_type', beverageType);
  return request(`/api/products/search?${params.toString()}`);
}

/**
 * Predict wine sensory quality rating via UCI ML model
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
 */
export async function checkBackendHealth(): Promise<{ status: string; version: string }> {
  return request<{ status: string; version: string }>('/api/health');
}
