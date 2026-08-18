import { useState } from 'react';
import {
  CheckCircle2,
  UploadCloud,
  Sparkles,
} from 'lucide-react';

interface DocumentItem {
  id: string;
  name: string;
  required: boolean;
  status: 'ready' | 'missing' | 'uploading';
  fileName?: string;
}

interface DocumentChecklistProps {
  schemeName?: string;
  documents?: string[];
}

export function DocumentChecklist({
  schemeName = 'Application Documents',
  documents = ['Aadhaar Card', 'Land Records (Khata/ROR)', 'Bank Passbook', 'Ration Card'],
}: DocumentChecklistProps) {
  const [docList, setDocList] = useState<DocumentItem[]>(() =>
    documents.map((doc, idx) => ({
      id: `doc-${idx}`,
      name: doc,
      required: true,
      status: idx === 0 ? 'ready' : 'missing', // 1st doc marked ready by default as demo
      fileName: idx === 0 ? 'Aadhaar_Verified.pdf' : undefined,
    }))
  );

  const readyCount = docList.filter((d) => d.status === 'ready').length;
  const totalCount = docList.length;
  const progressPercent = totalCount > 0 ? Math.round((readyCount / totalCount) * 100) : 0;

  const toggleDocStatus = (id: string) => {
    setDocList((prev) =>
      prev.map((doc) => {
        if (doc.id === id) {
          const nextStatus = doc.status === 'ready' ? 'missing' : 'ready';
          return {
            ...doc,
            status: nextStatus,
            fileName: nextStatus === 'ready' ? `${doc.name.replace(/\s+/g, '_')}.pdf` : undefined,
          };
        }
        return doc;
      })
    );
  };

  return (
    <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-5 text-left">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-base text-slate-900">Document Readiness Auditor</h3>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
              KagazCheck Ready
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit required certificates for {schemeName}
          </p>
        </div>

        <div className="text-right">
          <span className="text-xs font-bold text-slate-700">
            {readyCount} of {totalCount} Ready
          </span>
          <div className="w-32 bg-slate-100 h-2 rounded-full mt-1 overflow-hidden">
            <div
              className="bg-emerald-600 h-full rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Document Items List */}
      <div className="space-y-2.5">
        {docList.map((doc) => (
          <div
            key={doc.id}
            className={`p-3.5 rounded-2xl border transition-all flex items-center justify-between gap-3 ${
              doc.status === 'ready'
                ? 'bg-emerald-50/50 border-emerald-200 text-emerald-950'
                : 'bg-slate-50 border-slate-200 text-slate-800'
            }`}
          >
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => toggleDocStatus(doc.id)}
                className="focus:outline-none cursor-pointer"
              >
                {doc.status === 'ready' ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                ) : (
                  <div className="h-5 w-5 rounded-full border-2 border-slate-300 hover:border-emerald-500 transition" />
                )}
              </button>

              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold">{doc.name}</span>
                  {doc.required && (
                    <span className="text-[9px] font-semibold uppercase px-1.5 py-0.2 rounded bg-slate-200/80 text-slate-700">
                      Required
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500">
                  {doc.status === 'ready' ? (
                    <span className="text-emerald-700 font-mono text-[10px]">
                      ✓ {doc.fileName || 'Verified Document Attached'}
                    </span>
                  ) : (
                    'Not uploaded yet'
                  )}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => toggleDocStatus(doc.id)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-xl border transition cursor-pointer flex items-center gap-1.5 ${
                doc.status === 'ready'
                  ? 'border-emerald-200 bg-white text-emerald-800 hover:bg-emerald-50'
                  : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
              }`}
            >
              <UploadCloud className="h-3.5 w-3.5 text-slate-500" />
              <span>{doc.status === 'ready' ? 'Replace' : 'Upload'}</span>
            </button>
          </div>
        ))}
      </div>

      <div className="p-3 rounded-xl bg-slate-50 text-[11px] text-slate-500 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-emerald-600 shrink-0" />
        <span>
          Tip: Tap the circle to verify readiness or simulate document audit.
        </span>
      </div>
    </div>
  );
}
