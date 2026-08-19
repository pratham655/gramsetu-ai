import { useState } from 'react';
import {
  FileCheck,
  ExternalLink,
  ChevronRight,
  Sparkles,
  Info,
} from 'lucide-react';
import { DocumentChecklist } from './DocumentChecklist';

export interface ApplicationRecord {
  id: string;
  schemeId: string;
  schemeName: string;
  category: string;
  status: 'Not Started' | 'Preparing' | 'Documents Required' | 'Ready to Apply' | 'Submitted';
  documentsTotal: number;
  documentsReady: number;
  lastUpdated: string;
  nextAction: string;
  officialUrl: string;
  requiredDocuments: string[];
}

interface MyApplicationsViewProps {
  applications: ApplicationRecord[];
  onExploreSchemes: () => void;
  onOpenKagazCheck?: (schemeId?: string) => void;
}

export function MyApplicationsView({
  applications,
  onExploreSchemes,
  onOpenKagazCheck,
}: MyApplicationsViewProps) {
  const [selectedApp, setSelectedApp] = useState<ApplicationRecord | null>(
    applications[0] || null
  );

  const getStatusBadge = (status: ApplicationRecord['status']) => {
    switch (status) {
      case 'Submitted':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'Ready to Apply':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'Documents Required':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'Preparing':
        return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 text-left py-4">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200">
            <FileCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>Parchaa Application Lifecycle Tracker</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
            My Scheme Applications
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Track document audit readiness and submission stages for your matched schemes
          </p>
        </div>

        <button
          onClick={onExploreSchemes}
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs transition cursor-pointer"
        >
          <span>Find More Schemes</span>
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      {/* Prototype Context Notice */}
      <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200 text-amber-900 text-xs flex items-start gap-2.5">
        <Info className="h-4 w-4 text-amber-700 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="font-bold">Application Tracking Notice</p>
          <p className="text-amber-800 leading-relaxed">
            GramSetu AI prepares your statutory dossier and document readiness. Final statutory
            submissions are filed through official government portals (e.g. pmkisan.gov.in,
            awaassoft.nic.in) or your local Gram Panchayat / CSC Kendra.
          </p>
        </div>
      </div>

      {/* Applications Grid / Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Applications List */}
        <div className="lg:col-span-6 space-y-4">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Active Application Dossiers ({applications.length})
          </h3>

          {applications.map((app) => (
            <div
              key={app.id}
              onClick={() => setSelectedApp(app)}
              className={`p-5 rounded-2xl border transition-all cursor-pointer ${
                selectedApp?.id === app.id
                  ? 'bg-white border-emerald-500 ring-2 ring-emerald-500/10 shadow-sm'
                  : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                    {app.category}
                  </span>
                  <h4 className="font-bold text-sm text-slate-900 leading-snug">
                    {app.schemeName}
                  </h4>
                </div>

                <span
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${getStatusBadge(
                    app.status
                  )}`}
                >
                  {app.status}
                </span>
              </div>

              {/* Progress & Next Step */}
              <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[11px] text-slate-500">Documents:</span>
                  <p className="font-semibold text-slate-800">
                    {app.documentsReady} of {app.documentsTotal} Ready
                  </p>
                </div>
                <div>
                  <span className="text-[11px] text-slate-500">Next Action:</span>
                  <p className="font-semibold text-emerald-800 truncate" title={app.nextAction}>
                    {app.nextAction}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Right Column: Selected Application Dossier Details */}
        <div className="lg:col-span-6 space-y-6">
          {selectedApp ? (
            <div className="space-y-6">
              <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Dossier Details
                  </span>
                  <a
                    href={selectedApp.officialUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 inline-flex items-center gap-1"
                  >
                    <span>Ministry Portal</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>

                <div className="space-y-2">
                  <h3 className="font-extrabold text-lg text-slate-900">
                    {selectedApp.schemeName}
                  </h3>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <span>Last Updated: {selectedApp.lastUpdated}</span>
                    <span>·</span>
                    <span className="font-semibold text-slate-700">Status: {selectedApp.status}</span>
                  </div>
                </div>

                {/* Recommended Next Step Box */}
                <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200/80 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-950">
                    <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Recommended Next Step:</span>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {selectedApp.nextAction}
                  </p>
                </div>
              </div>

              {/* Document Checklist for this application */}
              <DocumentChecklist
                schemeName={selectedApp.schemeName}
                documents={selectedApp.requiredDocuments}
                onOpenKagazCheck={() => onOpenKagazCheck?.(selectedApp.schemeId)}
              />
            </div>
          ) : (
            <div className="p-12 text-center bg-white rounded-3xl border border-slate-200 text-slate-500 text-xs">
              Select an application to inspect the required document dossier.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
