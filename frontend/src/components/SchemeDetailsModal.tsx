import {
  X,
  CheckCircle2,
  XCircle,
  Building2,
  FileText,
  ExternalLink,
  ShieldCheck,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import type { SchemeData, SchemeMatchResult } from '../services/api';

interface SchemeDetailsModalProps {
  scheme: SchemeData | SchemeMatchResult | null;
  onClose: () => void;
  onStartApplication: (scheme: SchemeData | SchemeMatchResult) => void;
  onAuditDocuments?: (scheme: SchemeData | SchemeMatchResult) => void;
}

export function SchemeDetailsModal({
  scheme,
  onClose,
  onStartApplication,
  onAuditDocuments,
}: SchemeDetailsModalProps) {
  if (!scheme) return null;

  const isMatched = 'match_score' in scheme;
  const matchResult = isMatched ? (scheme as SchemeMatchResult) : null;
  const isEligible = matchResult?.eligible_status ?? false;

  const schemeName = 'name' in scheme ? scheme.name : scheme.scheme_name;
  const detailedDesc = scheme.detailed_description || scheme.short_description;
  const benefits = scheme.benefits || [];
  const requiredDocs = scheme.required_documents || [];
  const category = ('category' in scheme && scheme.category) ? scheme.category : 'Central & State Welfare';
  const state = ('state' in scheme && scheme.state) ? scheme.state : 'Central Government';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden text-left">
        {/* Modal Header */}
        <div className="px-6 sm:px-8 py-5 border-b border-slate-100 flex items-start justify-between gap-4 bg-slate-50/80">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-800">
                {state}
              </span>
              <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                {category}
              </span>
              {matchResult && (
                <span
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 ${
                    isEligible
                      ? 'bg-emerald-600 text-white'
                      : 'bg-amber-100 text-amber-900 border border-amber-200'
                  }`}
                >
                  {isEligible ? (
                    <>
                      <CheckCircle2 className="h-3 w-3" />
                      <span>100% Eligible</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-3 w-3 text-rose-500" />
                      <span>{matchResult.match_score}% Match Score</span>
                    </>
                  )}
                </span>
              )}
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 leading-tight">
              {schemeName}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-200/80 transition cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 sm:p-8 space-y-6 overflow-y-auto">
          {/* Scheme Overview */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Official Scheme Overview
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed font-normal">
              {detailedDesc}
            </p>
          </div>

          {/* Rule Breakdown (if evaluated) */}
          {matchResult && (
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-4">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                <span>Eligibility Verification Breakdown</span>
              </h3>

              <div className="space-y-3">
                {matchResult.matched_rules.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-bold text-emerald-800 flex items-center gap-1">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                      Why you qualify ({matchResult.matched_rules.length} conditions met):
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {matchResult.matched_rules.map((r, i) => (
                        <div
                          key={i}
                          className="text-xs p-2.5 rounded-xl bg-emerald-50 border border-emerald-100 text-emerald-950"
                        >
                          <p className="font-semibold">{r.description}</p>
                          <p className="text-[11px] text-emerald-700 mt-0.5">
                            Your Profile: <span className="font-mono font-medium">{String(r.actual_value)}</span>
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {matchResult.failed_rules.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    <span className="text-xs font-bold text-rose-800 flex items-center gap-1">
                      <XCircle className="h-3.5 w-3.5 text-rose-600" />
                      Unmet conditions ({matchResult.failed_rules.length} conditions pending):
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {matchResult.failed_rules.map((r, i) => (
                        <div
                          key={i}
                          className="text-xs p-2.5 rounded-xl bg-rose-50 border border-rose-100 text-rose-950"
                        >
                          <p className="font-semibold">{r.description}</p>
                          <p className="text-[11px] text-rose-700 mt-0.5">
                            Provided: <span className="font-mono">{String(r.actual_value ?? 'None')}</span> (Requires {r.operator} {String(r.expected_value)})
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Benefits */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Building2 className="h-4 w-4 text-emerald-600" />
              <span>Direct Entitlements &amp; Benefits</span>
            </h3>
            <div className="grid grid-cols-1 gap-2">
              {benefits.map((b, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2.5 p-3 rounded-xl bg-emerald-50/40 border border-emerald-100 text-xs text-slate-700 leading-relaxed"
                >
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>{b}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Required Documents */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="h-4 w-4 text-emerald-600" />
              <span>Required Application Documents</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {requiredDocs.map((doc, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs text-slate-800"
                >
                  <div className="h-2 w-2 rounded-full bg-emerald-500 shrink-0" />
                  <span className="font-medium">{doc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Official Verification Links */}
          <div className="pt-2 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              <span>Verified Government Gazette Data</span>
            </div>

            <div className="flex items-center gap-4">
              <a
                href={scheme.official_source_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 font-semibold text-emerald-700 hover:text-emerald-800"
              >
                <span>Official Scheme Portal</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>

              {scheme.application_url && (
                <a
                  href={scheme.application_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 font-semibold text-slate-700 hover:text-slate-900"
                >
                  <span>Direct Ministry Link</span>
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="p-6 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-slate-300 text-slate-700 font-semibold text-xs hover:bg-slate-100 transition cursor-pointer"
          >
            Close Details
          </button>

          <div className="flex flex-col sm:flex-row items-center gap-2.5 w-full sm:w-auto">
            {onAuditDocuments && (
              <button
                type="button"
                onClick={() => {
                  onAuditDocuments(scheme);
                  onClose();
                }}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-emerald-600 text-emerald-800 bg-emerald-50 hover:bg-emerald-100 font-bold text-xs shadow-2xs transition cursor-pointer flex items-center justify-center gap-1.5"
              >
                <span>Audit with KagazCheck</span>
              </button>
            )}

            <button
              onClick={() => {
                onStartApplication(scheme);
                onClose();
              }}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-200 flex items-center justify-center gap-2 transition cursor-pointer"
            >
              <Sparkles className="h-4 w-4" />
              <span>Prepare Application Dossier</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
