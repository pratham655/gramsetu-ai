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
  timeout: 30000,
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

// -------------------------------------------------------------
// VANI-BOT: MULTILINGUAL CONVERSATIONAL VOICE ENGINE INTERFACES
// -------------------------------------------------------------

export interface VaniSchemeCard {
  scheme_id: string;
  scheme_name: string;
  category?: string | null;
  state?: string | null;
  short_summary: string;
  eligible_status?: boolean | null;
  match_score?: number | null;
  key_benefits: string[];
  required_documents: string[];
  official_url: string;
  kagazcheck_ready: boolean;
}

export interface VaniActionLink {
  label: string;
  action_type: 'open_kagazcheck' | 'view_scheme' | 'check_eligibility' | 'open_url' | string;
  payload: Record<string, any>;
}

export interface VaniLanguageInfo {
  code: string;
  locale: string;
  name: string;
  native_name: string;
  supported_for_stt: boolean;
  supported_for_tts: boolean;
  sample_queries: string[];
}

export interface VaniTranscribeResponse {
  transcript: string;
  detected_language: string;
  confidence: number;
  status: string;
  duration_seconds?: number | null;
  provider: string;
  error_message?: string | null;
}

export interface VaniSpeakRequest {
  text: string;
  language?: string;
  speed?: number;
}

export interface VaniSpeakResponse {
  language: string;
  audio_base64?: string | null;
  mime_type: string;
  status: string;
  provider: string;
  message: string;
}

export interface VaniRespondRequest {
  query: string;
  language?: string;
  session_id?: string;
  citizen_profile?: CitizenProfile;
  context_scheme_id?: string;
  include_audio?: boolean;
}

export interface VaniRespondResponse {
  session_id: string;
  query: string;
  language: string;
  intent: string;
  reply_text: string;
  reply_audio_base64?: string | null;
  scheme_cards: VaniSchemeCard[];
  action_links: VaniActionLink[];
  sources: string[];
  suggested_followups: string[];
  context_scheme_id?: string | null;
}

export interface VaniConversationTurnRequest {
  session_id?: string;
  language: string;
  text_query?: string;
  audio_base64?: string;
  citizen_profile?: CitizenProfile;
  context_scheme_id?: string;
}

export interface VaniConversationTurnResponse {
  session_id: string;
  transcribed_query: string;
  detected_language: string;
  reply_text: string;
  reply_audio_base64?: string | null;
  scheme_cards: VaniSchemeCard[];
  action_links: VaniActionLink[];
  sources: string[];
  suggested_followups: string[];
}

/**
 * Vani-Bot: Transcribe recorded citizen audio clip to regional text
 */
export async function transcribeAudio(
  file: File | Blob,
  language: string = 'kn'
): Promise<VaniTranscribeResponse> {
  const formData = new FormData();
  formData.append('file', file, 'voice_recording.webm');
  formData.append('language', language);

  const response = await apiClient.post<VaniTranscribeResponse>(
    '/api/v1/vanibot/transcribe',
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
 * Vani-Bot: Submit multilingual query and retrieve grounded civic answer with scheme cards
 */
export async function respondVani(
  req: VaniRespondRequest
): Promise<VaniRespondResponse> {
  const response = await apiClient.post<VaniRespondResponse>(
    '/api/v1/vanibot/respond',
    req
  );
  return response.data;
}

/**
 * Vani-Bot: Synthesize text into regional spoken audio
 */
export async function speakVaniText(
  req: VaniSpeakRequest
): Promise<VaniSpeakResponse> {
  const response = await apiClient.post<VaniSpeakResponse>(
    '/api/v1/vanibot/speak',
    req
  );
  return response.data;
}

/**
 * Vani-Bot: Execute unified conversation turn (audio/text -> audio/cards reply)
 */
export async function converseVani(
  req: VaniConversationTurnRequest
): Promise<VaniConversationTurnResponse> {
  const response = await apiClient.post<VaniConversationTurnResponse>(
    '/api/v1/vanibot/conversation',
    req
  );
  return response.data;
}

/**
 * Vani-Bot: Get supported Indian regional languages catalog
 */
export async function fetchVaniLanguages(): Promise<VaniLanguageInfo[]> {
  const response = await apiClient.get<VaniLanguageInfo[]>(
    '/api/v1/vanibot/languages'
  );
  return response.data;
}

/**
 * Vani-Bot: Clear multi-turn conversation session memory
 */
export async function clearVaniSession(
  sessionId: string
): Promise<{ status: string; message: string }> {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  const response = await apiClient.post<{ status: string; message: string }>(
    '/api/v1/vanibot/session/clear',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

// -------------------------------------------------------------
// PARCHAA GENERATOR: APPLICATION DOSSIER GENERATOR INTERFACES
// -------------------------------------------------------------

export interface ParchaaCitizenProfile {
  name?: string | null;
  state?: string | null;
  district?: string | null;
  occupation?: string | null;
  age?: number | null;
  gender?: string | null;
  income?: number | null;
  landholding?: number | null;
  category?: string | null;
  bpl?: boolean | null;
  aadhaar_masked?: string | null;
  bank_account_masked?: string | null;
  yojanamatch_eligible?: boolean | null;
  yojanamatch_score?: number | null;
}

export interface ParchaaDocumentItem {
  document_name: string;
  document_code?: string | null;
  status: 'Ready' | 'Verified' | 'Missing' | 'Needs Attention' | 'Required';
  required: boolean;
  enclosure_note?: string | null;
  action_needed?: string | null;
}

export interface ParchaaOffice {
  office_name: string;
  department: string;
  address?: string | null;
  district?: string | null;
  state?: string | null;
  contact_info?: string | null;
  is_verified: boolean;
  unverified_notice?: string | null;
}

export interface ParchaaTimeline {
  expected_days?: number | null;
  timeline_description: string;
  is_verified: boolean;
  unverified_notice?: string | null;
}

export interface ParchaaSchemeSummary {
  scheme_id: string;
  scheme_name: string;
  category: string;
  short_description: string;
  detailed_description: string;
  target_beneficiaries: string;
  main_benefits: string[];
  eligibility_summary: string[];
  official_source_url: string;
  application_url?: string | null;
}

export interface ParchaaApplicationInfo {
  application_channel: string;
  official_portal_url?: string | null;
  physical_enclosures: string[];
  process_steps: string[];
  administrative_office: ParchaaOffice;
  processing_timeline: ParchaaTimeline;
  next_step_action: string;
}

export interface ParchaaRequest {
  scheme_id: string;
  citizen_profile?: ParchaaCitizenProfile | CitizenProfile | null;
  application_context?: Record<string, any> | null;
  document_readiness?: ParchaaDocumentItem[] | null;
  kagazcheck_ready_count?: number | null;
  kagazcheck_total_count?: number | null;
  preferred_language?: string | null;
}

export interface ParchaaResponse {
  parchaa_id: string;
  reference_number: string;
  generated_at: string;
  scheme: ParchaaSchemeSummary;
  citizen?: ParchaaCitizenProfile | null;
  documents: ParchaaDocumentItem[];
  application_info: ParchaaApplicationInfo;
  pdf_base64?: string | null;
  pdf_filename: string;
  page_count: number;
  language: string;
}

/**
 * Parchaa Generator: Compile application dossier with single-page PDF
 */
export async function generateParchaa(
  req: ParchaaRequest
): Promise<ParchaaResponse> {
  const response = await apiClient.post<ParchaaResponse>(
    '/api/v1/parchaa/generate',
    req
  );
  return response.data;
}

/**
 * Parchaa Generator: Stream raw application dossier PDF for browser download
 */
export async function downloadParchaaPdf(
  req: ParchaaRequest
): Promise<Blob> {
  const response = await apiClient.post(
    '/api/v1/parchaa/download',
    req,
    {
      responseType: 'blob',
    }
  );
  return response.data;
}

/**
 * Parchaa Generator: Fetch structured scheme preview before generation
 */
export async function fetchParchaaPreview(
  schemeId: string,
  language: string = 'en'
): Promise<ParchaaResponse> {
  const response = await apiClient.get<ParchaaResponse>(
    `/api/v1/parchaa/preview/${schemeId}`,
    {
      params: { language },
    }
  );
  return response.data;
}

export { API_BASE_URL };


