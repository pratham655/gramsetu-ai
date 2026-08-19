import {
  Search,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  UserCheck,
  Cpu,
  Landmark,
  CheckCircle2,
  Mic,
} from 'lucide-react';

interface HeroProps {
  onFindSchemes: () => void;
  onExploreSchemes: () => void;
  onOpenVaniBot?: () => void;
}

export function Hero({ onFindSchemes, onExploreSchemes, onOpenVaniBot }: HeroProps) {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-emerald-50/60 via-slate-50 to-slate-50 pt-10 pb-16 border-b border-slate-200/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Hero Content */}
          <div className="lg:col-span-7 space-y-6 text-left">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-100/80 text-emerald-800 text-xs font-semibold border border-emerald-200 shadow-xs">
              <ShieldCheck className="h-4 w-4 text-emerald-700" />
              <span>Official Government Welfare Assistance Platform</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-[1.15]">
              Find Government Schemes <br className="hidden sm:inline" />
              <span className="text-emerald-700">You May Be Eligible For</span>
            </h1>

            <p className="text-slate-600 text-base sm:text-lg leading-relaxed max-w-2xl font-normal">
              GramSetu AI helps citizens discover relevant government welfare schemes,
              understand eligibility with deterministic accuracy, and prepare the exact documents needed to apply.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={onFindSchemes}
                className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm shadow-md shadow-emerald-200 hover:shadow-lg transition-all transform hover:-translate-y-0.5 cursor-pointer"
              >
                <Search className="h-4 w-4" />
                <span>Find My Schemes</span>
                <ArrowRight className="h-4 w-4" />
              </button>

              {onOpenVaniBot && (
                <button
                  onClick={onOpenVaniBot}
                  className="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-900 border border-emerald-300 font-semibold text-sm shadow-xs transition-colors cursor-pointer"
                >
                  <Mic className="h-4 w-4 text-emerald-600 animate-pulse" />
                  <span>Speak with Vani-Bot</span>
                </button>
              )}

              <button
                onClick={onExploreSchemes}
                className="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 font-semibold text-sm shadow-xs transition-colors cursor-pointer"
              >
                <BookOpen className="h-4 w-4 text-slate-500" />
                <span>Explore Schemes</span>
              </button>
            </div>


            {/* Quick Civic Assurance Badges */}
            <div className="pt-6 border-t border-slate-200/80 grid grid-cols-3 gap-4 text-left">
              <div>
                <div className="flex items-center gap-1 text-emerald-700 font-bold text-lg">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>100% Free</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">No brokers or agent fees</p>
              </div>

              <div>
                <div className="flex items-center gap-1 text-slate-800 font-bold text-lg">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Instant Match</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">Rule-based scoring engine</p>
              </div>

              <div>
                <div className="flex items-center gap-1 text-slate-800 font-bold text-lg">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Direct Portals</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">Official ministry links</p>
              </div>
            </div>
          </div>

          {/* Right Hero Diagram / Visual Card */}
          <div className="lg:col-span-5">
            <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200 shadow-md space-y-6 relative">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  The GramSetu Journey
                </span>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Citizen-First
                </span>
              </div>

              {/* Connected Steps Diagram */}
              <div className="space-y-3">
                {/* Step 1 */}
                <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
                  <div className="h-10 w-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm shrink-0">
                    <UserCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">1. Citizen Profile</h4>
                    <p className="text-[11px] text-slate-500">Age, Occupation, Land, State, Income</p>
                  </div>
                </div>

                {/* Connector */}
                <div className="flex justify-center">
                  <div className="h-4 w-0.5 bg-emerald-300"></div>
                </div>

                {/* Step 2 */}
                <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-emerald-50/80 border border-emerald-200">
                  <div className="h-10 w-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-xs">
                    <Cpu className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-emerald-900">2. GramSetu Rule Engine</h4>
                    <p className="text-[11px] text-emerald-700">Deterministic criteria verification</p>
                  </div>
                </div>

                {/* Connector */}
                <div className="flex justify-center">
                  <div className="h-4 w-0.5 bg-emerald-300"></div>
                </div>

                {/* Step 3 */}
                <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
                  <div className="h-10 w-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-sm shrink-0">
                    <Landmark className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">3. Government Welfare Delivery</h4>
                    <p className="text-[11px] text-slate-500">PM-KISAN, PMAY-G, PM-JAY &amp; State Subsidies</p>
                  </div>
                </div>
              </div>

              <div className="pt-2 text-center">
                <button
                  onClick={onFindSchemes}
                  className="text-xs font-bold text-emerald-700 hover:text-emerald-800 inline-flex items-center gap-1 cursor-pointer"
                >
                  <span>Check what schemes you qualify for today</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
