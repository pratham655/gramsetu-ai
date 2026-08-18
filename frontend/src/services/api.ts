import axios, { type AxiosInstance } from 'axios';

// API base URL configured from environment variable with fallback
const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface HealthCheckResponse {
  status: string;
  service: string;
}

export interface CitizenProfile {
  age?: number;
  income?: number;
  state?: string;
  district?: string;
  gender?: string;
  occupation?: string;
  landholding?: number;
  category?: string;
  bpl?: boolean;
}

export interface RuleEvaluationResult {
  field: string;
  operator: string;
  expected_value: unknown;
  actual_value: unknown;
  passed: boolean;
  description?: string;
}

export interface SchemeMatchResult {
  scheme_id: string;
  scheme_name: string;
  short_description?: string;
  detailed_description?: string;
  match_score: number;
  eligible_status: boolean;
  matched_rules: RuleEvaluationResult[];
  failed_rules: RuleEvaluationResult[];
  benefits: string[];
  required_documents: string[];
  official_source_url: string;
  application_url?: string;
  category?: string;
  state?: string | null;
}

export interface EligibilityMatchResponse {
  citizen_profile: CitizenProfile;
  total_schemes_evaluated: number;
  eligible_schemes_count: number;
  results: SchemeMatchResult[];
}

export interface SchemeData {
  id: string;
  name: string;
  short_description: string;
  detailed_description: string;
  benefits: string[];
  state?: string | null;
  category?: string | null;
  occupation?: string | null;
  official_source_url: string;
  application_url?: string | null;
  required_documents: string[];
  active: boolean;
  rules?: {
    id?: string;
    field: string;
    operator: string;
    value: string;
    description?: string;
  }[];
}

// Axios instance with default settings
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

/**
 * Health check service to verify backend connectivity
 */
export async function checkBackendHealth(): Promise<{
  data: HealthCheckResponse;
  responseTimeMs: number;
}> {
  const startTime = performance.now();
  const response = await apiClient.get<HealthCheckResponse>('/api/v1/health');
  const responseTimeMs = Math.round(performance.now() - startTime);

  return {
    data: response.data,
    responseTimeMs,
  };
}

/**
 * YojanaMatch service to evaluate citizen profile eligibility
 */
export async function matchEligibility(
  profile: CitizenProfile
): Promise<EligibilityMatchResponse> {
  const response = await apiClient.post<EligibilityMatchResponse>(
    '/api/v1/eligibility/match',
    profile
  );
  return response.data;
}

/**
 * Fetch all active government schemes from backend database
 */
export async function fetchActiveSchemes(): Promise<SchemeData[]> {
  const response = await apiClient.get<SchemeData[]>('/api/v1/eligibility/schemes');
  return response.data;
}

export { API_BASE_URL };
