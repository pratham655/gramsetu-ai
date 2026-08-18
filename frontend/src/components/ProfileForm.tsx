import { useState, type FormEvent } from 'react';
import {
  Search,
  Sparkles,
  User,
  MapPin,
  Briefcase,
  RefreshCw,
  Info,
} from 'lucide-react';
import type { CitizenProfile } from '../services/api';

interface ProfileFormProps {
  initialProfile: CitizenProfile;
  onSubmit: (profile: CitizenProfile) => void;
  loading: boolean;
}

export function ProfileForm({ initialProfile, onSubmit, loading }: ProfileFormProps) {
  const [profile, setProfile] = useState<CitizenProfile>(initialProfile);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit(profile);
  };

  const loadPreset = (preset: 'farmer_karnataka' | 'rural_mother' | 'youth_artisan') => {
    if (preset === 'farmer_karnataka') {
      const p: CitizenProfile = {
        age: 42,
        income: 180000,
        state: 'Karnataka',
        district: 'Tumakuru',
        gender: 'male',
        occupation: 'farmer',
        landholding: 2.5,
        category: 'OBC',
        bpl: true,
      };
      setProfile(p);
      onSubmit(p);
    } else if (preset === 'rural_mother') {
      const p: CitizenProfile = {
        age: 25,
        income: 240000,
        state: 'Uttar Pradesh',
        district: 'Varanasi',
        gender: 'female',
        occupation: 'homemaker',
        landholding: 0,
        category: 'General',
        bpl: false,
      };
      setProfile(p);
      onSubmit(p);
    } else if (preset === 'youth_artisan') {
      const p: CitizenProfile = {
        age: 21,
        income: 90000,
        state: 'Rajasthan',
        district: 'Jaipur',
        gender: 'female',
        occupation: 'artisan',
        landholding: 0,
        category: 'SC',
        bpl: true,
      };
      setProfile(p);
      onSubmit(p);
    }
  };

  return (
    <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
      {/* Header */}
      <div className="space-y-2 border-b border-slate-100 pb-5 text-left">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200/70">
          <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
          <span>YojanaMatch Intelligent Profiler</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Find Schemes You're Eligible For
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          Tell us a little about yourself. GramSetu AI will compare your profile against
          verified statutory scheme rules deterministically.
        </p>
      </div>

      {/* Test Sample Profiles */}
      <div className="space-y-2 bg-slate-50 p-4 rounded-2xl border border-slate-200/80 text-left">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <Info className="h-3.5 w-3.5 text-emerald-600" />
            <span>Quick Sample Profiles</span>
          </span>
          <span className="text-[10px] text-slate-500">Tap to auto-fill &amp; test</span>
        </div>
        <div className="flex flex-wrap gap-2 pt-1">
          <button
            type="button"
            onClick={() => loadPreset('farmer_karnataka')}
            className="text-xs px-3 py-1.5 rounded-xl bg-white hover:bg-emerald-50 hover:text-emerald-900 hover:border-emerald-300 text-slate-700 font-semibold border border-slate-200 shadow-2xs transition cursor-pointer"
          >
            🌾 Small Farmer (Karnataka, BPL)
          </button>
          <button
            type="button"
            onClick={() => loadPreset('rural_mother')}
            className="text-xs px-3 py-1.5 rounded-xl bg-white hover:bg-emerald-50 hover:text-emerald-900 hover:border-emerald-300 text-slate-700 font-semibold border border-slate-200 shadow-2xs transition cursor-pointer"
          >
            🤰 Expectant Mother (UP)
          </button>
          <button
            type="button"
            onClick={() => loadPreset('youth_artisan')}
            className="text-xs px-3 py-1.5 rounded-xl bg-white hover:bg-emerald-50 hover:text-emerald-900 hover:border-emerald-300 text-slate-700 font-semibold border border-slate-200 shadow-2xs transition cursor-pointer"
          >
            🛠️ Artisan / BPL (Rajasthan)
          </button>
        </div>
      </div>

      {/* Profile Questionnaire Form */}
      <form onSubmit={handleSubmit} className="space-y-6 text-left">
        {/* Section 1: Personal Demographics */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1.5">
            <User className="h-3.5 w-3.5 text-emerald-600" />
            <span>1. Personal &amp; Geographic Information</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Age (in years)
              </label>
              <input
                type="number"
                min="0"
                max="120"
                value={profile.age ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    age: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                placeholder="e.g. 42"
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Gender</label>
              <select
                value={profile.gender ?? ''}
                onChange={(e) =>
                  setProfile({ ...profile, gender: e.target.value || undefined })
                }
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white transition"
              >
                <option value="">-- Select Gender --</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                State of Residence
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={profile.state ?? ''}
                  onChange={(e) =>
                    setProfile({ ...profile, state: e.target.value || undefined })
                  }
                  placeholder="e.g. Karnataka, Uttar Pradesh"
                  className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
                />
                <MapPin className="h-4 w-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                District / Taluk
              </label>
              <input
                type="text"
                value={profile.district ?? ''}
                onChange={(e) =>
                  setProfile({ ...profile, district: e.target.value || undefined })
                }
                placeholder="e.g. Tumakuru, Varanasi"
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Socio-Economic Profile */}
        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1.5">
            <Briefcase className="h-3.5 w-3.5 text-emerald-600" />
            <span>2. Occupation &amp; Household Economics</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Primary Occupation
              </label>
              <input
                type="text"
                value={profile.occupation ?? ''}
                onChange={(e) =>
                  setProfile({ ...profile, occupation: e.target.value || undefined })
                }
                placeholder="e.g. farmer, artisan, student"
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Annual Household Income (₹)
              </label>
              <input
                type="number"
                min="0"
                step="1000"
                value={profile.income ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    income: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                placeholder="e.g. 180000"
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Agricultural Landholding (Acres)
              </label>
              <input
                type="number"
                min="0"
                step="0.1"
                value={profile.landholding ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    landholding: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                placeholder="e.g. 2.5 (0 if landless)"
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Social Category
              </label>
              <select
                value={profile.category ?? ''}
                onChange={(e) =>
                  setProfile({ ...profile, category: e.target.value || undefined })
                }
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white transition"
              >
                <option value="">-- Select Category --</option>
                <option value="General">General</option>
                <option value="OBC">OBC (Other Backward Classes)</option>
                <option value="SC">SC (Scheduled Caste)</option>
                <option value="ST">ST (Scheduled Tribe)</option>
              </select>
            </div>
          </div>

          <div className="pt-2">
            <label className="block text-xs font-semibold text-slate-700 mb-2">
              Do you hold a Below Poverty Line (BPL) or Antyodaya Ration Card?
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label
                className={`flex items-center gap-2.5 p-3 rounded-xl border cursor-pointer transition ${
                  profile.bpl === true
                    ? 'border-emerald-500 bg-emerald-50/50 text-emerald-900 font-semibold'
                    : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                <input
                  type="radio"
                  name="bpl_opt"
                  checked={profile.bpl === true}
                  onChange={() => setProfile({ ...profile, bpl: true })}
                  className="text-emerald-600 focus:ring-emerald-500 h-4 w-4"
                />
                <span className="text-xs">Yes (BPL / SECC Card Holder)</span>
              </label>

              <label
                className={`flex items-center gap-2.5 p-3 rounded-xl border cursor-pointer transition ${
                  profile.bpl === false
                    ? 'border-emerald-500 bg-emerald-50/50 text-emerald-900 font-semibold'
                    : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                <input
                  type="radio"
                  name="bpl_opt"
                  checked={profile.bpl === false}
                  onChange={() => setProfile({ ...profile, bpl: false })}
                  className="text-emerald-600 focus:ring-emerald-500 h-4 w-4"
                />
                <span className="text-xs">No / Non-BPL</span>
              </label>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t border-slate-100">
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md shadow-emerald-200 hover:shadow-lg transition-all disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Evaluating Eligibility Rules...</span>
              </>
            ) : (
              <>
                <Search className="h-4 w-4" />
                <span>Find My Eligible Schemes</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
