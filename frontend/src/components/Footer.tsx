import { Compass, ShieldCheck, ExternalLink } from 'lucide-react';

interface FooterProps {
  onNavigateTab: (tab: 'home' | 'find' | 'explore' | 'profile' | 'applications') => void;
}

export function Footer({ onNavigateTab }: FooterProps) {
  return (
    <footer className="bg-slate-900 text-slate-300 pt-14 pb-8 border-t border-slate-800 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand & Mission */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-emerald-600 flex items-center justify-center text-white font-bold shadow-md shadow-emerald-900/50">
                <Compass className="h-5 w-5" />
              </div>
              <div>
                <span className="font-extrabold text-lg text-white tracking-tight">
                  Gram<span className="text-emerald-400">Setu</span> AI
                </span>
                <p className="text-[11px] text-slate-400">ग्रामीण नागरिक सेतु</p>
              </div>
            </div>

            <p className="text-slate-400 leading-relaxed text-xs max-w-md">
              GramSetu AI is an AI-powered civic assistance platform empowering Indian citizens to
              discover welfare schemes, understand statutory eligibility deterministically,
              verify required documentation, and receive step-by-step application guidance.
            </p>

            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-[11px] text-emerald-400">
              <ShieldCheck className="h-4 w-4" />
              <span>Grounded in Official Government Gazettes &amp; Portals</span>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-3">
            <h4 className="font-semibold text-white uppercase tracking-wider text-xs">
              Quick Access
            </h4>
            <ul className="space-y-2 text-slate-400">
              <li>
                <button
                  onClick={() => onNavigateTab('find')}
                  className="hover:text-emerald-400 transition cursor-pointer"
                >
                  Find My Eligible Schemes
                </button>
              </li>
              <li>
                <button
                  onClick={() => onNavigateTab('explore')}
                  className="hover:text-emerald-400 transition cursor-pointer"
                >
                  Explore Central &amp; State Schemes
                </button>
              </li>
              <li>
                <button
                  onClick={() => onNavigateTab('applications')}
                  className="hover:text-emerald-400 transition cursor-pointer"
                >
                  Application Tracking Checklist
                </button>
              </li>
              <li>
                <button
                  onClick={() => onNavigateTab('profile')}
                  className="hover:text-emerald-400 transition cursor-pointer"
                >
                  Citizen Profile &amp; Preferences
                </button>
              </li>
            </ul>
          </div>

          {/* Verified Official Resources */}
          <div className="space-y-3">
            <h4 className="font-semibold text-white uppercase tracking-wider text-xs">
              Official Portals
            </h4>
            <ul className="space-y-2 text-slate-400">
              <li>
                <a
                  href="https://www.india.gov.in"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 hover:text-emerald-400 transition"
                >
                  <span>National Portal of India</span>
                  <ExternalLink className="h-3 w-3 text-slate-500" />
                </a>
              </li>
              <li>
                <a
                  href="https://dbtbharat.gov.in"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 hover:text-emerald-400 transition"
                >
                  <span>DBT Bharat Direct Transfer</span>
                  <ExternalLink className="h-3 w-3 text-slate-500" />
                </a>
              </li>
              <li>
                <a
                  href="https://pmkisan.gov.in"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 hover:text-emerald-400 transition"
                >
                  <span>PM-KISAN Samman Nidhi</span>
                  <ExternalLink className="h-3 w-3 text-slate-500" />
                </a>
              </li>
              <li>
                <a
                  href="https://nha.gov.in/PM-JAY"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 hover:text-emerald-400 transition"
                >
                  <span>Ayushman Bharat PM-JAY</span>
                  <ExternalLink className="h-3 w-3 text-slate-500" />
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-500">
          <p>© {new Date().getFullYear()} GramSetu AI · Citizen Welfare Intelligence</p>
          <div className="flex items-center gap-4">
            <span>Free &amp; Open Civic Technology</span>
            <span>·</span>
            <span>Zero Brokerage / Zero Intermediary Policy</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
