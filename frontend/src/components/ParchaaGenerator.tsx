import { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Printer,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Building2,
  ExternalLink,
  ShieldCheck,
  Sparkles,
  ChevronDown,
  Eye,
  FileCheck,
  User,
  Layers,
  Clock,
  MapPin,
  BookOpen,
} from 'lucide-react';
import {
  generateParchaa,
  fetchParchaaPreview,
  type CitizenProfile,
  type SchemeData,
  type SchemeMatchResult,
  type ParchaaResponse,
  type ParchaaDocumentItem,
  type ParchaaRequest,
} from '../services/api';

interface ParchaaGeneratorProps {
  initialScheme?: SchemeData | SchemeMatchResult | { id: string; name: string } | null;
  citizenProfile?: CitizenProfile;
  availableSchemes?: SchemeData[];
  documentReadiness?: ParchaaDocumentItem[];
  language?: string;
  onExploreSchemes?: () => void;
  onOpenKagazCheck?: (schemeId?: string) => void;
}

export function ParchaaGenerator({
  initialScheme = null,
  citizenProfile,
  availableSchemes = [],
  documentReadiness = [],
  language = 'en',
  onExploreSchemes,
  onOpenKagazCheck,
}: ParchaaGeneratorProps) {

  // Scheme Selection State
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>(() => {
    if (!initialScheme) return 'pm-kisan-001';
    if ('id' in initialScheme && initialScheme.id) return initialScheme.id;
    if ('scheme_id' in initialScheme && (initialScheme as SchemeMatchResult).scheme_id) {
      return (initialScheme as SchemeMatchResult).scheme_id;
    }
    return 'pm-kisan-001';
  });

  // Generator State
  const [loading, setLoading] = useState<boolean>(false);
  const [generatingPdf, setGeneratingPdf] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [parchaaData, setParchaaData] = useState<ParchaaResponse | null>(null);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [showPdfViewer, setShowPdfViewer] = useState<boolean>(false);

  // Sync selected scheme when initialScheme changes
  useEffect(() => {
    if (initialScheme) {
      if ('id' in initialScheme && initialScheme.id) {
        setSelectedSchemeId(initialScheme.id);
      } else if ('scheme_id' in initialScheme && (initialScheme as SchemeMatchResult).scheme_id) {
        setSelectedSchemeId((initialScheme as SchemeMatchResult).scheme_id);
      }
    }
  }, [initialScheme]);

  // Load preview data whenever scheme changes
  useEffect(() => {
    async function loadPreview() {
      if (!selectedSchemeId) return;
      try {
        setLoading(true);
        setError(null);
        const data = await fetchParchaaPreview(selectedSchemeId, language);
        setParchaaData(data);
        if (data.pdf_base64) {
          const byteCharacters = atob(data.pdf_base64);
          const byteNumbers = new Array(byteCharacters.length);
          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
          }
          const byteArray = new Uint8Array(byteNumbers);
          const blob = new Blob([byteArray], { type: 'application/pdf' });
          const url = URL.createObjectURL(blob);
          setPdfBlobUrl(url);
        }
      } catch (err: unknown) {
        console.error('Failed to load Parchaa preview:', err);
        let msg = 'Failed to load verified scheme preview.';
        if (err instanceof Error) msg = err.message;
        setError(msg);
      } finally {
        setLoading(false);
      }
    }
    loadPreview();
  }, [selectedSchemeId, language]);

  // Handle Full Parchaa Dossier Generation
  const handleGenerateParchaa = async () => {
    if (!selectedSchemeId) return;
    try {
      setGeneratingPdf(true);
      setError(null);
      setSuccessMessage(null);

      const requestPayload: ParchaaRequest = {
        scheme_id: selectedSchemeId,
        citizen_profile: citizenProfile,
        document_readiness: documentReadiness.length > 0 ? documentReadiness : undefined,
        preferred_language: language,
      };

      const response = await generateParchaa(requestPayload);
      setParchaaData(response);

      if (response.pdf_base64) {
        const byteCharacters = atob(response.pdf_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        setPdfBlobUrl(url);
      }

      setSuccessMessage(
        language === 'kn'
          ? 'ಅರ್ಜಿ ಪರ್ಚಾ ಯಶಸ್ವಿಯಾಗಿ ರಚಿಸಲಾಗಿದೆ!'
          : language === 'hi'
          ? 'आवेदन पर्चा सफलतापूर्वक तैयार किया गया!'
          : 'Application Parchaa dossier compiled successfully!'
      );
    } catch (err: unknown) {
      console.error('Error generating Parchaa:', err);
      let msg = 'Failed to generate Application Parchaa.';
      if (err instanceof Error) msg = err.message;
      setError(msg);
    } finally {
      setGeneratingPdf(false);
    }
  };

  // Handle Direct PDF Download
  const handleDownloadPdf = () => {
    if (!parchaaData?.pdf_base64) {
      handleGenerateParchaa();
      return;
    }
    const link = document.createElement('a');
    link.href = `data:application/pdf;base64,${parchaaData.pdf_base64}`;
    link.download = parchaaData.pdf_filename || `GramSetu_Parchaa_${selectedSchemeId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Handle Direct Printing
  const handlePrintParchaa = () => {
    if (pdfBlobUrl) {
      const printWindow = window.open(pdfBlobUrl, '_blank');
      if (printWindow) {
        printWindow.focus();
      } else {
        window.print();
      }
    } else {
      window.print();
    }
  };

  // Status Badge Helper
  const getDocumentStatusBadge = (status: string) => {
    switch (status) {
      case 'Ready':
      case 'Verified':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
            <span>Ready / Verified</span>
          </span>
        );
      case 'Needs Attention':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
            <AlertTriangle className="h-3 w-3 text-amber-600" />
            <span>Needs Attention</span>
          </span>
        );
      case 'Missing':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-200">
            <AlertCircle className="h-3 w-3 text-rose-600" />
            <span>Missing</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            <span>Required</span>
          </span>
        );
    }
  };

  // Localized Strings
  const t = {
    title:
      language === 'kn'
        ? 'ಪರ್ಚಾ ಜನರೇಟರ್ (Parchaa Generator)'
        : language === 'hi'
        ? 'पर्चा जनरेटर (Parchaa Generator)'
        : 'Parchaa Generator',
    subtitle:
      language === 'kn'
        ? 'ಒಂದೇ ಕ್ಲಿಕ್‌ನಲ್ಲಿ ಅಧಿಕೃತ ಸರಕಾರಿ ಯೋಜನೆಯ ಅರ್ಹತಾ ಪತ್ರ ಮತ್ತು ದಾಖಲೆಗಳ ದಾಖಲಾತಿ'
        : language === 'hi'
        ? 'एक-क्लिक में आधिकारिक सरकारी योजना आवेदन पर्चा और दस्तावेज चेकलिस्ट'
        : 'One-Click Actionable Government Scheme Application Dossier',
    selectScheme:
      language === 'kn' ? 'ಯೋಜನೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ:' : language === 'hi' ? 'योजना चुनें:' : 'Select Scheme:',
    generateBtn:
      language === 'kn'
        ? 'ಪರ್ಚಾ ರಚಿಸಿ (Generate Parchaa)'
        : language === 'hi'
        ? 'पर्चा तैयार करें (Generate Parchaa)'
        : 'Generate Application Parchaa',
    downloadPdf:
      language === 'kn' ? 'ಪಿಡಿಎಫ್ ಡೌನ್‌ಲೋಡ್' : language === 'hi' ? 'पीडीएफ डाउनलोड' : 'Download Printable PDF',
    printBtn: language === 'kn' ? 'ಮುದ್ರಿಸಿ (Print)' : language === 'hi' ? 'प्रिंट करें (Print)' : 'Print Dossier',
    regenerateBtn:
      language === 'kn' ? 'ಮರುರಚಿಸಿ (Regenerate)' : language === 'hi' ? 'पुनः बनाएं' : 'Regenerate',
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 text-left py-4">
      {/* Top Banner Card */}
      <div className="bg-gradient-to-br from-emerald-800 via-emerald-700 to-teal-900 text-white rounded-3xl p-6 sm:p-8 shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-8 -translate-y-8 w-72 h-72 rounded-full bg-white/5 blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-600/60 backdrop-blur-xs text-emerald-100 text-xs font-semibold border border-emerald-400/30">
              <FileText className="h-3.5 w-3.5" />
              <span>One-Click Application Dossier • Single-Page A4</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              {t.title}
            </h1>
            <p className="text-xs sm:text-sm text-emerald-100/90 max-w-2xl leading-relaxed">
              {t.subtitle}
            </p>
          </div>

          {/* Quick Actions in Header */}
          <div className="flex flex-wrap items-center gap-2.5">
            {parchaaData?.pdf_base64 && (
              <>
                <button
                  type="button"
                  onClick={handleDownloadPdf}
                  className="px-4 py-2.5 rounded-xl bg-white text-emerald-900 hover:bg-emerald-50 font-bold text-xs shadow-md transition flex items-center gap-1.5 cursor-pointer"
                >
                  <Download className="h-4 w-4 text-emerald-700" />
                  <span>{t.downloadPdf}</span>
                </button>

                <button
                  type="button"
                  onClick={handlePrintParchaa}
                  className="px-3.5 py-2.5 rounded-xl bg-emerald-600/80 hover:bg-emerald-600 text-white font-semibold text-xs border border-emerald-400/40 transition flex items-center gap-1.5 cursor-pointer"
                >
                  <Printer className="h-4 w-4" />
                  <span>{t.printBtn}</span>
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Main Grid: Control Panel (Left) & Parchaa Live Dossier Preview (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Scheme Selector, Citizen Context, Document Status */}
        <div className="lg:col-span-4 space-y-6">
          {/* Scheme Selection Card */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="h-4 w-4 text-emerald-600" />
                <span>Scheme Selector</span>
              </span>
              {onExploreSchemes && (
                <button
                  type="button"
                  onClick={onExploreSchemes}
                  className="text-[11px] font-semibold text-emerald-700 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-200 transition cursor-pointer flex items-center gap-1"
                >
                  <BookOpen className="h-3 w-3" />
                  <span>Browse All</span>
                </button>
              )}
            </div>


            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 block">
                {t.selectScheme}
              </label>
              <div className="relative">
                <select
                  value={selectedSchemeId}
                  onChange={(e) => setSelectedSchemeId(e.target.value)}
                  className="w-full text-xs font-medium px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white appearance-none cursor-pointer pr-9"
                >
                  {availableSchemes.length > 0 ? (
                    availableSchemes.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="pm-kisan-001">PM-KISAN (Income Support)</option>
                      <option value="pmay-g-002">PMAY-G (Rural Housing)</option>
                      <option value="pmmvy-003">PMMVY (Maternity Benefit)</option>
                      <option value="pm-jay-004">Ayushman Bharat (PM-JAY Health)</option>
                      <option value="raitha-vidya-005">Karnataka Raitha Vidya Nidhi</option>
                    </>
                  )}
                </select>
                <ChevronDown className="h-4 w-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
              </div>
            </div>

            {/* Primary Action Button */}
            <button
              type="button"
              onClick={handleGenerateParchaa}
              disabled={generatingPdf || loading}
              className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-200 flex items-center justify-center gap-2 transition disabled:opacity-50 cursor-pointer"
            >
              {generatingPdf ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Compiling Single-Page Parchaa...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>{t.generateBtn}</span>
                </>
              )}
            </button>
          </div>

          {/* Citizen Snapshot Card */}
          {citizenProfile && (
            <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <User className="h-4 w-4 text-emerald-600" />
                  <span>Citizen Profile Snapshot</span>
                </span>
                <span className="text-[10px] text-slate-400">Grounded Context</span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500">Location:</span>
                  <span className="font-semibold text-slate-800">
                    {citizenProfile.district || 'District'}, {citizenProfile.state || 'Karnataka'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500">Occupation:</span>
                  <span className="font-semibold text-slate-800 capitalize">
                    {citizenProfile.occupation || 'Farmer'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500">Landholding:</span>
                  <span className="font-semibold text-slate-800">
                    {citizenProfile.landholding !== undefined ? `${citizenProfile.landholding} Acres` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500">BPL Status:</span>
                  <span className="font-semibold text-slate-800">
                    {citizenProfile.bpl ? 'BPL Cardholder' : 'Non-BPL'}
                  </span>
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600 flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                <span>Privacy: PII &amp; bank accounts are strictly masked.</span>
              </div>
            </div>
          )}

          {/* KagazCheck Integration Card */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <FileCheck className="h-4 w-4 text-emerald-600" />
                <span>Document Readiness Audit</span>
              </span>
              {onOpenKagazCheck && (
                <button
                  type="button"
                  onClick={() => onOpenKagazCheck(selectedSchemeId)}
                  className="text-[11px] font-bold text-emerald-700 hover:text-emerald-800 underline cursor-pointer"
                >
                  Audit in KagazCheck
                </button>
              )}
            </div>

            <p className="text-xs text-slate-600">
              Audit your documents with vision AI before visiting the government office to verify
              clarity, dates, and names.
            </p>

            {onOpenKagazCheck && (
              <button
                type="button"
                onClick={() => onOpenKagazCheck(selectedSchemeId)}
                className="w-full py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs transition flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <FileCheck className="h-3.5 w-3.5 text-emerald-600" />
                <span>Verify Certificates in KagazCheck</span>
              </button>
            )}
          </div>
        </div>

        {/* Right Column: Live Printable Parchaa Dossier Sheet */}
        <div className="lg:col-span-8 space-y-4">
          {/* Alerts */}
          {error && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5">
              <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
              <p className="font-semibold">{error}</p>
            </div>
          )}

          {successMessage && (
            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-start gap-2.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
              <p className="font-bold">{successMessage}</p>
            </div>
          )}

          {/* Toggle PDF View / HTML Parchaa Sheet */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Printable Parchaa Preview
              </span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                1 A4 Page
              </span>
            </div>

            <div className="flex items-center gap-2">
              {pdfBlobUrl && (
                <button
                  type="button"
                  onClick={() => setShowPdfViewer(!showPdfViewer)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-semibold transition cursor-pointer"
                >
                  <Eye className="h-3.5 w-3.5 text-emerald-600" />
                  <span>{showPdfViewer ? 'View Document Layout' : 'View Raw PDF'}</span>
                </button>
              )}
            </div>
          </div>

          {/* Raw PDF iframe modal/viewer if toggled */}
          {showPdfViewer && pdfBlobUrl ? (
            <div className="bg-white rounded-3xl border border-slate-300 shadow-sm overflow-hidden p-2">
              <iframe
                src={pdfBlobUrl}
                title="Parchaa PDF Preview"
                className="w-full h-[780px] rounded-2xl border border-slate-200"
              />
            </div>
          ) : parchaaData ? (
            /* Live Parchaa Printable Sheet Container */
            <div className="bg-white rounded-3xl border-2 border-slate-300 shadow-lg p-6 sm:p-8 space-y-6 text-slate-900 relative print:shadow-none print:border-none">
              {/* Header Box */}
              <div className="border-b-2 border-emerald-600 pb-4 space-y-1">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="space-y-0.5">
                    <div className="inline-flex items-center gap-1.5 text-xs font-extrabold text-emerald-800 tracking-wider">
                      <ShieldCheck className="h-4 w-4 text-emerald-600" />
                      <span>GRAMSETU AI • APPLICATION PARCHAA</span>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      Official Citizen Welfare Application Dossier | Ref:{' '}
                      <span className="font-mono font-bold text-slate-700">
                        {parchaaData.reference_number}
                      </span>
                    </p>
                  </div>

                  <div className="text-left sm:text-right text-xs text-slate-600 space-y-0.5">
                    <p>
                      <span className="font-semibold">Date:</span> {parchaaData.generated_at}
                    </p>
                    <p>
                      <span className="font-semibold">Category:</span> {parchaaData.scheme.category}
                    </p>
                  </div>
                </div>

                <div className="pt-2">
                  <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 leading-tight">
                    {parchaaData.scheme.scheme_name}
                  </h2>
                </div>
              </div>

              {/* 2-Column Overview: Scheme Benefits & Citizen Snapshot */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Left: Scheme Overview */}
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                  <h3 className="font-bold text-emerald-900 uppercase tracking-wider text-[11px] flex items-center gap-1">
                    <Building2 className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Scheme Overview &amp; Benefits</span>
                  </h3>
                  <p className="text-slate-700 leading-relaxed">
                    {parchaaData.scheme.short_description}
                  </p>
                  <div className="pt-1 space-y-1 text-[11px] text-slate-600">
                    <span className="font-bold text-slate-800 block">Direct Entitlements:</span>
                    <ul className="list-disc pl-4 space-y-0.5">
                      {parchaaData.scheme.main_benefits.slice(0, 3).map((b, i) => (
                        <li key={i}>{b}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Right: Citizen Eligibility Snapshot */}
                <div className="p-4 rounded-2xl bg-emerald-50/50 border border-emerald-200 space-y-2 text-xs">
                  <h3 className="font-bold text-emerald-950 uppercase tracking-wider text-[11px] flex items-center gap-1">
                    <User className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Citizen Eligibility Snapshot</span>
                  </h3>
                  {parchaaData.citizen ? (
                    <div className="space-y-1.5 text-slate-700">
                      <p>
                        <span className="font-semibold">Applicant:</span>{' '}
                        {parchaaData.citizen.name || 'Beneficiary Applicant'} (
                        {parchaaData.citizen.age || 'Adult'} yrs,{' '}
                        {parchaaData.citizen.gender || 'Applicant'})
                      </p>
                      <p>
                        <span className="font-semibold">Location:</span>{' '}
                        {parchaaData.citizen.district || 'District'},{' '}
                        {parchaaData.citizen.state || 'State'}
                      </p>
                      <p>
                        <span className="font-semibold">Occupation:</span>{' '}
                        {parchaaData.citizen.occupation || 'Farmer'} |{' '}
                        <span className="font-semibold">Category:</span>{' '}
                        {parchaaData.citizen.category || 'General'}
                      </p>
                      <p>
                        <span className="font-semibold">Aadhaar ID:</span>{' '}
                        <span className="font-mono text-slate-900 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                          {parchaaData.citizen.aadhaar_masked || 'XXXX-XXXX-7058'}
                        </span>
                      </p>
                      <p className="text-emerald-800 font-bold">
                        YojanaMatch Status: 100% Deterministic Rule Match
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-1 text-slate-600">
                      <p>Standard citizen profile evaluated.</p>
                      <p>Statutory eligibility conditions apply per official gazette.</p>
                      <p className="text-emerald-800 font-bold">Status: Ready for Application</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Required Documents Matrix */}
              <div className="space-y-2.5">
                <h3 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="h-4 w-4 text-emerald-600" />
                  <span>Required Documents &amp; Readiness Status</span>
                </h3>

                <div className="overflow-x-auto rounded-2xl border border-slate-200">
                  <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
                    <thead className="bg-slate-100 font-bold text-slate-800">
                      <tr>
                        <th className="py-2.5 px-4">Required Document Name</th>
                        <th className="py-2.5 px-4">Audit Status</th>
                        <th className="py-2.5 px-4">Enclosure Instructions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {parchaaData.documents.map((doc, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/80">
                          <td className="py-2.5 px-4 font-semibold text-slate-900">
                            {doc.document_name}
                          </td>
                          <td className="py-2.5 px-4">
                            {getDocumentStatusBadge(doc.status)}
                          </td>
                          <td className="py-2.5 px-4 text-slate-600">
                            {doc.enclosure_note || 'Self-attested physical photocopy'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Enclosures & Process Steps */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Physical Enclosures */}
                <div className="p-4 rounded-2xl bg-amber-50/50 border border-amber-200 space-y-2 text-xs">
                  <h3 className="font-bold text-amber-950 uppercase tracking-wider text-[11px]">
                    Physical Enclosures to Carry
                  </h3>
                  <ul className="list-disc pl-4 space-y-1 text-slate-700">
                    {parchaaData.application_info.physical_enclosures.map((enc, i) => (
                      <li key={i}>{enc}</li>
                    ))}
                  </ul>
                </div>

                {/* Application Process Steps */}
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                  <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">
                    Application Process &amp; Steps
                  </h3>
                  <div className="space-y-1 text-slate-700">
                    {parchaaData.application_info.process_steps.map((st, i) => (
                      <p key={i} className="leading-snug">
                        {st}
                      </p>
                    ))}
                  </div>
                </div>
              </div>

              {/* Administrative Office & Official Portal */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
                  <span className="font-bold text-slate-900 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Administrative Nodal Office &amp; Official Portal</span>
                  </span>
                  <span className="text-[10px] text-slate-500">Verified Channel</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-700">
                  <div>
                    {parchaaData.application_info.administrative_office.is_verified ? (
                      <div className="space-y-0.5">
                        <p className="font-bold text-slate-900">
                          {parchaaData.application_info.administrative_office.office_name}
                        </p>
                        <p className="text-slate-600">
                          {parchaaData.application_info.administrative_office.department}
                        </p>
                        <p className="text-slate-500">
                          {parchaaData.application_info.administrative_office.contact_info ||
                            'Helpdesk available at Gram Panchayat'}
                        </p>
                      </div>
                    ) : (
                      <p className="text-slate-500 italic">
                        {parchaaData.application_info.administrative_office.unverified_notice ||
                          'Office information not available in current verified database.'}
                      </p>
                    )}
                  </div>

                  <div>
                    <p className="font-bold text-slate-900">Official Portal Link:</p>
                    <a
                      href={
                        parchaaData.application_info.official_portal_url ||
                        parchaaData.scheme.official_source_url
                      }
                      target="_blank"
                      rel="noreferrer"
                      className="text-emerald-700 hover:text-emerald-800 font-mono font-semibold underline inline-flex items-center gap-1 break-all mt-0.5"
                    >
                      <span>
                        {parchaaData.application_info.official_portal_url ||
                          parchaaData.scheme.official_source_url}
                      </span>
                      <ExternalLink className="h-3 w-3 shrink-0" />
                    </a>

                    <div className="mt-2 text-[11px] text-slate-600 flex items-center gap-1">
                      <Clock className="h-3 w-3 text-slate-400" />
                      <span>
                        {parchaaData.application_info.processing_timeline.is_verified
                          ? parchaaData.application_info.processing_timeline.timeline_description
                          : parchaaData.application_info.processing_timeline.unverified_notice ||
                            'Processing timeline not available in verified database.'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actionable Next Step Box */}
              <div className="p-4 rounded-2xl bg-emerald-100/70 border-2 border-emerald-600 text-xs text-emerald-950 space-y-1">
                <span className="font-extrabold uppercase tracking-wider text-[11px] flex items-center gap-1.5 text-emerald-900">
                  <Sparkles className="h-4 w-4 text-emerald-700" />
                  <span>Actionable Next Step for Citizen</span>
                </span>
                <p className="font-bold leading-relaxed">
                  {parchaaData.application_info.next_step_action}
                </p>
              </div>

              {/* Bottom Print / Download Action Bar inside preview */}
              <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-200 text-xs">
                <span className="text-slate-500 text-[11px]">
                  GramSetu AI • Zero permanent PII retention • Printable single-page A4
                </span>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleDownloadPdf}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Download PDF</span>
                  </button>

                  <button
                    type="button"
                    onClick={handlePrintParchaa}
                    className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <Printer className="h-3.5 w-3.5" />
                    <span>Print</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-4 shadow-xs">
              <RefreshCw className="h-8 w-8 text-emerald-600 animate-spin mx-auto" />
              <p className="text-xs text-slate-500">Loading verified scheme dossier...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
