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

export interface FieldValidationResult {
  field: string;
  label: string;
  extracted_value?: string | null;
  is_valid: boolean;
  rule_description: string;
  issue_reason?: string | null;
}

export interface ProfileMatchItem {
  field: string;
  profile_value?: string | null;
  document_value?: string | null;
  matched: boolean;
  confidence: number;
  details: string;
}

export interface DocumentAnalysisResult {
  document_id: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  document_type: string;
  document_type_code: string;
  document_type_confidence: number;
  is_detected: boolean;
  is_readable: boolean;
  image_quality_score: number;
  extracted_fields: Record<string, any>;
  fields_validation: FieldValidationResult[];
  validity_status: 'VALID' | 'WARNING' | 'INVALID' | 'EXPIRED';
  citizen_details_match: 'MATCH' | 'PARTIAL_MATCH' | 'MISMATCH' | 'UNVERIFIED';
  profile_match_details: ProfileMatchItem[];
  overall_status: 'VALID' | 'WARNING' | 'INVALID';
  summary_notes: string[];
  recommended_action: string;
}

export interface ChecklistItem {
  document_code: string;
  document_name: string;
  required: boolean;
  status: 'VALID' | 'WARNING' | 'MISSING' | 'INVALID';
  uploaded_document_id?: string | null;
  details: string;
  action_needed: string;
}

export interface SchemeReadinessAudit {
  scheme_id: string;
  scheme_name: string;
  total_required_docs: number;
  ready_docs_count: number;
  readiness_percentage: number;
  is_ready_to_apply: boolean;
  checklist: ChecklistItem[];
  critical_missing_docs: string[];
  overall_recommendation: string;
}

export interface DocumentTypeSpecification {
  code: string;
  name: string;
  aliases: string[];
  required_fields: string[];
  description: string;
  validity_period_years?: number | null;
  sample_hints: string[];
}

export interface KagazCheckAnalyzeResponse {
  document_result: DocumentAnalysisResult;
  scheme_readiness?: SchemeReadinessAudit | null;
}

/**
 * KagazCheck: Analyze and audit document image or PDF
 */
export async function analyzeDocument(
  file: File | Blob,
  fileName: string = 'document.jpg',
  schemeId?: string,
  citizenProfile?: CitizenProfile
): Promise<KagazCheckAnalyzeResponse> {
  const formData = new FormData();
  formData.append('file', file, fileName);
  if (schemeId) {
    formData.append('scheme_id', schemeId);
  }
  if (citizenProfile) {
    formData.append('citizen_profile', JSON.stringify(citizenProfile));
  }

  const response = await apiClient.post<KagazCheckAnalyzeResponse>(
    '/api/v1/kagazcheck/analyze',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

/**
 * KagazCheck: Audit scheme readiness across documents
 */
export async function auditSchemeReadiness(
  schemeId: string,
  documentIds?: string[]
): Promise<SchemeReadinessAudit> {
  const response = await apiClient.post<SchemeReadinessAudit>(
    '/api/v1/kagazcheck/audit',
    {
      scheme_id: schemeId,
      document_ids: documentIds || [],
    }
  );
  return response.data;
}

/**
 * KagazCheck: Fetch supported government document catalog
 */
export async function fetchSupportedDocumentTypes(): Promise<DocumentTypeSpecification[]> {
  const response = await apiClient.get<DocumentTypeSpecification[]>(
    '/api/v1/kagazcheck/document-types'
  );
  return response.data;
}

/**
 * KagazCheck: Clear in-memory session document audit store
 */
export async function clearKagazCheckSession(): Promise<{ status: string; message: string }> {
  const response = await apiClient.post<{ status: string; message: string }>(
    '/api/v1/kagazcheck/session/clear'
  );
  return response.data;
}

export { API_BASE_URL };
