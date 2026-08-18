import { useState, type FormEvent } from 'react';
import {
  User,
  Briefcase,
  Save,
  Search,
  CheckCircle2,
} from 'lucide-react';
import type { CitizenProfile } from '../services/api';

interface MyProfileViewProps {
  profile: CitizenProfile;
  onSaveProfile: (profile: CitizenProfile) => void;
  onFindSchemes: (profile: CitizenProfile) => void;
}

export function MyProfileView({
  profile: initialProfile,
  onSaveProfile,
  onFindSchemes,
}: MyProfileViewProps) {
  const [profile, setProfile] = useState<CitizenProfile>(initialProfile);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const handleSave = (e: FormEvent) => {
    e.preventDefault();
    onSaveProfile(profile);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 text-left py-4">
      {/* Profile Header */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-emerald-700 to-emerald-500 text-white font-black text-2xl flex items-center justify-center shadow-md shadow-emerald-200">
            <User className="h-8 w-8" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
              Citizen Profile &amp; Preferences
            </h2>
            <p className="text-xs sm:text-sm text-slate-500">
              Keep your profile updated for instant welfare scheme eligibility checks
            </p>
          </div>
        </div>

        <button
          onClick={() => onFindSchemes(profile)}
          className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm shadow-emerald-200 transition cursor-pointer"
        >
          <Search className="h-4 w-4" />
          <span>Find Matching Schemes</span>
        </button>
      </div>

      {savedSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          <span>Citizen profile saved successfully! Ready for eligibility matching.</span>
        </div>
      )}

      {/* Profile Editor Form */}
      <form onSubmit={handleSave} className="space-y-6">
        {/* Personal Details */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs space-y-5">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <User className="h-4 w-4 text-emerald-600" />
            <span>Personal Information</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Age</label>
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
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Gender</label>
              <select
                value={profile.gender ?? ''}
                onChange={(e) =>
                  setProfile({ ...profile, gender: e.target.value || undefined })
                }
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
              >
                <option value="">-- Select --</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">State</label>
              <input
                type="text"
                value={profile.state ?? ''}
                onChange={(e) =>
                  setProfile({ ...profile, state: e.target.value || undefined })
                }
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">District</label>
              <input
                type="text"
                value={profile.district ?? ''}
                onChange={(e) =>
                  setProfile({ ...profile, district: e.target.value || undefined })
                }
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* Economic Details */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs space-y-5">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <Briefcase className="h-4 w-4 text-emerald-600" />
            <span>Socio-Economic &amp; Landholdings</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Occupation
              </label>
              <input
                type="text"
                value={profile.occupation ?? ''}
                onChange={(e) =>
                  setProfile({ ...profile, occupation: e.target.value || undefined })
                }
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Annual Household Income (₹)
              </label>
              <input
                type="number"
                value={profile.income ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    income: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Landholding (Acres)
              </label>
              <input
                type="number"
                step="0.1"
                value={profile.landholding ?? ''}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    landholding: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Category
              </label>
              <select
                value={profile.category ?? ''}
                onChange={(e) =>
                  setProfile({ ...profile, category: e.target.value || undefined })
                }
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
              >
                <option value="">-- Select --</option>
                <option value="General">General</option>
                <option value="OBC">OBC</option>
                <option value="SC">SC</option>
                <option value="ST">ST</option>
              </select>
            </div>
          </div>

          <div className="pt-2">
            <label className="block text-xs font-semibold text-slate-700 mb-2">
              BPL / SECC Card Status
            </label>
            <div className="flex gap-4">
              <label className="inline-flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="prof_bpl"
                  checked={profile.bpl === true}
                  onChange={() => setProfile({ ...profile, bpl: true })}
                  className="text-emerald-600 focus:ring-emerald-500"
                />
                <span>Yes (BPL Card Holder)</span>
              </label>
              <label className="inline-flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="radio"
                  name="prof_bpl"
                  checked={profile.bpl === false}
                  onChange={() => setProfile({ ...profile, bpl: false })}
                  className="text-emerald-600 focus:ring-emerald-500"
                />
                <span>No</span>
              </label>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="submit"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow-xs transition cursor-pointer"
          >
            <Save className="h-4 w-4" />
            <span>Update Profile</span>
          </button>
        </div>
      </form>
    </div>
  );
}
