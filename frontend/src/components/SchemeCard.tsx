import {
  CheckCircle2,
  XCircle,
  Building2,
  FileText,
  ExternalLink,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import type { SchemeData, SchemeMatchResult } from '../services/api';

interface SchemeCardProps {
  scheme: SchemeData | SchemeMatchResult;
  onViewDetails: (scheme: SchemeData | SchemeMatchResult) => void;
  onCheckEligibility?: () => void;
  isMatchedView?: boolean;
}

export function SchemeCard({
  scheme,
  onViewDetails,
  onCheckEligibility,
  isMatchedView = false,
}: SchemeCardProps) {
  const matchResult = isMatchedView ? (scheme as SchemeMatchResult) : null;
  const isEligible = matchResult?.eligible_status ?? false;
  const matchScore = matchResult?.match_score ?? null;

  const schemeName = 'name' in scheme ? scheme.name : scheme.scheme_name;
  const shortDesc = scheme.short_description;
  const benefits = scheme.benefits || [];
  const requiredDocs = scheme.required_documents || [];
  const category = ('category' in scheme && scheme.category) ? scheme.category : 'General Welfare';
  const state = ('state' in scheme && scheme.state) ? scheme.state : 'Central Government';

  return (
    <div
      className={`bg-white rounded-2xl border transition-all duration-200 p-6 flex flex-col justify-between hover:shadow-md ${
        isMatchedView
          ? isEligible
            ? 'border-emerald-300 ring-1 ring-emerald-500/10 shadow-xs'
            : 'border-slate-200/90 bg-slate-50/50'
          : 'border-slate-200 shadow-xs'
      }`}
    >
      <div className="space-y-4">
        {/* Top Badges */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
              {state}
            </span>
            <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-100">
              {category}
            </span>
          </div>

          {matchScore !== null && (
            <div>
              {isEligible ? (
                <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-600 text-white shadow-xs">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Eligible (100%)</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-slate-200 text-slate-700">
                  <XCircle className="h-3.5 w-3.5 text-rose-500" />
                  <span>{matchScore}% Match</span>
                </span>
              )}
            </div>
          )}
        </div>

        {/* Title & Description */}
        <div className="space-y-1.5">
          <h3 className="font-bold text-base text-slate-900 leading-snug line-clamp-2">
            {schemeName}
          </h3>
          <p className="text-xs text-slate-600 leading-relaxed line-clamp-3">
            {shortDesc}
          </p>
        </div>

        {/* Rule Breakdown for Matched View */}
        {isMatchedView && matchResult && (
          <div className="pt-2 border-t border-slate-100 space-y-2">
            {matchResult.matched_rules.length > 0 && (
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                  Matched Criteria ({matchResult.matched_rules.length})
                </span>
                <div className="flex flex-wrap gap-1">
                  {matchResult.matched_rules.map((r, i) => (
                    <span
                      key={i}
                      className="text-[11px] bg-emerald-50 text-emerald-900 border border-emerald-100 px-2 py-0.5 rounded-md"
                      title={`${r.field}: ${String(r.actual_value)}`}
                    >
                      {r.description || `${r.field} ${r.operator} ${String(r.expected_value)}`}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {matchResult.failed_rules.length > 0 && (
              <div className="space-y-1 pt-1">
                <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1">
                  <XCircle className="h-3 w-3 text-rose-600" />
                  Why this didn't match ({matchResult.failed_rules.length})
                </span>
                <div className="flex flex-wrap gap-1">
                  {matchResult.failed_rules.map((r, i) => (
                    <span
                      key={i}
                      className="text-[11px] bg-rose-50 text-rose-900 border border-rose-100 px-2 py-0.5 rounded-md"
                      title={`Provided: ${String(r.actual_value ?? 'None')}`}
                    >
                      {r.description || `Requires ${r.field} ${r.operator} ${String(r.expected_value)}`}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Primary Benefit Highlight */}
        {benefits.length > 0 && (
          <div className="p-3 rounded-xl bg-emerald-50/50 border border-emerald-100/80 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-900">
              <Building2 className="h-3.5 w-3.5 text-emerald-700" />
              <span>Key Benefit:</span>
            </div>
            <p className="text-xs text-slate-700 line-clamp-2 leading-relaxed">
              {benefits[0]}
            </p>
          </div>
        )}

        {/* Required Documents Badge Count */}
        {requiredDocs.length > 0 && (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <FileText className="h-3.5 w-3.5 text-slate-400 shrink-0" />
            <span>
              {requiredDocs.length} required documents ({requiredDocs.slice(0, 2).join(', ')}
              {requiredDocs.length > 2 ? '...' : ''})
            </span>
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
        <button
          onClick={() => onViewDetails(scheme)}
          className="text-xs font-bold text-slate-700 hover:text-emerald-700 inline-flex items-center gap-1 transition cursor-pointer"
        >
          <span>View Details</span>
          <ChevronRight className="h-3.5 w-3.5" />
        </button>

        {isMatchedView ? (
          <button
            onClick={() => onViewDetails(scheme)}
            className={`text-xs font-semibold px-3.5 py-2 rounded-xl transition cursor-pointer flex items-center gap-1.5 ${
              isEligible
                ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
            }`}
          >
            <span>{isEligible ? 'Prepare Application' : 'Inspect Criteria'}</span>
            <ChevronRight className="h-3 w-3" />
          </button>
        ) : onCheckEligibility ? (
          <button
            onClick={onCheckEligibility}
            className="text-xs font-semibold px-3.5 py-2 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 transition cursor-pointer flex items-center gap-1.5"
          >
            <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
            <span>Check Eligibility</span>
          </button>
        ) : (
          <a
            href={scheme.official_source_url}
            target="_blank"
            rel="noreferrer"
            className="text-xs font-medium text-slate-500 hover:text-slate-900 inline-flex items-center gap-1"
          >
            <span>Official Portal</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
    </div>
  );
}
