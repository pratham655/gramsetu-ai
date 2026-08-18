import { useState } from 'react';
import { Landmark, ArrowRight } from 'lucide-react';
import { SchemeCard } from './SchemeCard';
import type { SchemeData, SchemeMatchResult } from '../services/api';

interface PopularSchemesProps {
  schemes: SchemeData[];
  loading: boolean;
  onViewDetails: (scheme: SchemeData | SchemeMatchResult) => void;
  onCheckEligibility: () => void;
}

export function PopularSchemes({
  schemes,
  loading,
  onViewDetails,
  onCheckEligibility,
}: PopularSchemesProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const categories = [
    'All',
    'Agriculture',
    'Housing & Rural Development',
    'Health & Social Protection',
    'Women & Child Development',
    'Education & Agriculture',
  ];

  const filteredSchemes =
    selectedCategory === 'All'
      ? schemes
      : schemes.filter((s) => s.category?.toLowerCase().includes(selectedCategory.toLowerCase()));

  return (
    <section className="py-16 bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="space-y-2 text-left">
            <div className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-800 uppercase tracking-widest">
              <Landmark className="h-4 w-4" />
              <span>Government Schemes Directory</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Popular Government Welfare Schemes
            </h2>
            <p className="text-slate-600 text-sm max-w-2xl">
              Verified statutory programs for farmers, rural families, mothers, and students.
            </p>
          </div>

          <button
            onClick={onCheckEligibility}
            className="inline-flex items-center gap-2 text-xs font-bold text-emerald-700 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 px-4 py-2.5 rounded-xl transition cursor-pointer"
          >
            <span>Match Your Profile</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-emerald-700 text-white shadow-xs'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Schemes Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-64 rounded-2xl bg-slate-200 animate-pulse border border-slate-200"
              />
            ))}
          </div>
        ) : filteredSchemes.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSchemes.map((scheme) => (
              <SchemeCard
                key={scheme.id}
                scheme={scheme}
                onViewDetails={onViewDetails}
                onCheckEligibility={onCheckEligibility}
                isMatchedView={false}
              />
            ))}
          </div>
        ) : (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-500 text-xs">
            No schemes found in this category.
          </div>
        )}
      </div>
    </section>
  );
}
