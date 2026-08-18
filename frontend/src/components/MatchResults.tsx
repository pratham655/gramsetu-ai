import { useState } from 'react';
import { CheckCircle2, AlertCircle, Sparkles, Filter } from 'lucide-react';
import { SchemeCard } from './SchemeCard';
import type { EligibilityMatchResponse, SchemeData, SchemeMatchResult } from '../services/api';

interface MatchResultsProps {
  matchData: EligibilityMatchResponse;
  onViewDetails: (scheme: SchemeData | SchemeMatchResult) => void;
  onEditProfile: () => void;
}

export function MatchResults({
  matchData,
  onViewDetails,
  onEditProfile,
}: MatchResultsProps) {
  const [filter, setFilter] = useState<'all' | 'eligible' | 'partial'>('all');

  const { results, eligible_schemes_count, total_schemes_evaluated, citizen_profile } =
    matchData;

  const filteredResults = results.filter((r) => {
    if (filter === 'eligible') return r.eligible_status;
    if (filter === 'partial') return !r.eligible_status;
    return true;
  });

  return (
    <div className="space-y-6 text-left">
      {/* Result Headline Banner */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200">
              <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
              <span>YojanaMatch Evaluation Complete</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Your Scheme Matches
            </h2>
            <p className="text-xs sm:text-sm text-slate-600">
              <span className="font-bold text-emerald-700 text-sm">
                {eligible_schemes_count} of {total_schemes_evaluated} schemes
              </span>{' '}
              fully matched your profile attributes.
            </p>
          </div>

          <button
            onClick={onEditProfile}
            className="text-xs font-semibold px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer self-start sm:self-auto"
          >
            Modify Profile
          </button>
        </div>

        {/* Profile Summary Chips */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-600">
          <span className="font-semibold text-slate-700">Evaluated Profile:</span>
          {citizen_profile.age && (
            <span className="bg-slate-100 px-2 py-0.5 rounded-md">{citizen_profile.age} yrs</span>
          )}
          {citizen_profile.occupation && (
            <span className="bg-slate-100 px-2 py-0.5 rounded-md capitalize">
              {citizen_profile.occupation}
            </span>
          )}
          {citizen_profile.state && (
            <span className="bg-slate-100 px-2 py-0.5 rounded-md">{citizen_profile.state}</span>
          )}
          {citizen_profile.income !== undefined && (
            <span className="bg-slate-100 px-2 py-0.5 rounded-md">
              ₹{citizen_profile.income.toLocaleString()} / yr
            </span>
          )}
          {citizen_profile.landholding !== undefined && (
            <span className="bg-slate-100 px-2 py-0.5 rounded-md">
              {citizen_profile.landholding} acres land
            </span>
          )}
          {citizen_profile.bpl !== undefined && (
            <span className="bg-slate-100 px-2 py-0.5 rounded-md">
              {citizen_profile.bpl ? 'BPL Card Holder' : 'Non-BPL'}
            </span>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <div className="flex gap-1.5">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                filter === 'all'
                  ? 'bg-slate-900 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              All Evaluated ({results.length})
            </button>
            <button
              onClick={() => setFilter('eligible')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1 ${
                filter === 'eligible'
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'bg-white text-emerald-800 hover:bg-emerald-50 border border-emerald-200'
              }`}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>Eligible Schemes ({eligible_schemes_count})</span>
            </button>
            <button
              onClick={() => setFilter('partial')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1 ${
                filter === 'partial'
                  ? 'bg-slate-900 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              <AlertCircle className="h-3.5 w-3.5 text-amber-500" />
              <span>Unmet Criteria ({results.length - eligible_schemes_count})</span>
            </button>
          </div>
        </div>
      </div>

      {/* Scheme Cards Grid */}
      {filteredResults.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredResults.map((scheme) => (
            <SchemeCard
              key={scheme.scheme_id}
              scheme={scheme}
              onViewDetails={onViewDetails}
              isMatchedView={true}
            />
          ))}
        </div>
      ) : (
        <div className="p-12 text-center bg-white rounded-3xl border border-slate-200 text-slate-500 space-y-2">
          <AlertCircle className="h-8 w-8 text-slate-400 mx-auto" />
          <p className="text-sm font-semibold text-slate-700">No schemes match this filter</p>
          <p className="text-xs text-slate-500">
            Try adjusting your filter selection or modifying your citizen profile.
          </p>
        </div>
      )}
    </div>
  );
}
