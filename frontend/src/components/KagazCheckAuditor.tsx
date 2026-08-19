import { useState, useRef, useEffect } from 'react';
import {
  Camera,
  UploadCloud,
  FileCheck,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Sparkles,
  ShieldCheck,
  RotateCcw,
  Layers,
  ArrowRight,
  Info,
  RefreshCw,
  X,
  FileText,
} from 'lucide-react';
import {
  analyzeDocument,
  fetchSupportedDocumentTypes,
  type CitizenProfile,
  type SchemeData,
  type SchemeMatchResult,
  type DocumentAnalysisResult,
  type SchemeReadinessAudit,
  type DocumentTypeSpecification,
  type KagazCheckAnalyzeResponse,
} from '../services/api';

interface KagazCheckAuditorProps {
  initialScheme?: SchemeData | SchemeMatchResult | { id: string; name: string; required_documents: string[] } | null;
  citizenProfile?: CitizenProfile;
  onApplyForScheme?: (schemeId: string) => void;
  onGenerateParchaa?: (schemeId: string) => void;
  availableSchemes?: SchemeData[];
}

export function KagazCheckAuditor({
  initialScheme = null,
  citizenProfile,
  onApplyForScheme,
  onGenerateParchaa,
  availableSchemes = [],
}: KagazCheckAuditorProps) {

  const [selectedSchemeId, setSelectedSchemeId] = useState<string>(() => {
    if (!initialScheme) return 'pm-kisan-001';
    if ('id' in initialScheme && initialScheme.id) return initialScheme.id;
    if ('scheme_id' in initialScheme && (initialScheme as SchemeMatchResult).scheme_id) {
      return (initialScheme as SchemeMatchResult).scheme_id;
    }
    return 'pm-kisan-001';
  });

  // Input Mode: 'camera' | 'upload'
  const [inputMode, setInputMode] = useState<'camera' | 'upload'>('upload');

  // Camera State
  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment');
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Processing & Results State
  const [processing, setProcessing] = useState<boolean>(false);
  const [processingStep, setProcessingStep] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [latestResult, setLatestResult] = useState<DocumentAnalysisResult | null>(null);
  const [schemeReadiness, setSchemeReadiness] = useState<SchemeReadinessAudit | null>(null);
  const [auditHistory, setAuditHistory] = useState<DocumentAnalysisResult[]>([]);

  // Document Specifications Catalog
  const [docSpecs, setDocSpecs] = useState<DocumentTypeSpecification[]>([]);

  // Load Document Catalog on Mount
  useEffect(() => {
    async function loadCatalog() {
      try {
        const specs = await fetchSupportedDocumentTypes();
        setDocSpecs(specs);
      } catch (err) {
        console.error('Failed to load document catalog:', err);
      }
    }
    loadCatalog();
  }, []);

  // Update selected scheme if initialScheme changes
  useEffect(() => {
    if (initialScheme) {
      if ('id' in initialScheme && initialScheme.id) {
        setSelectedSchemeId(initialScheme.id);
      } else if ('scheme_id' in initialScheme && (initialScheme as SchemeMatchResult).scheme_id) {
        setSelectedSchemeId((initialScheme as SchemeMatchResult).scheme_id);
      }
    }
  }, [initialScheme]);

  // Handle Camera Initialization
  const startCamera = async () => {
    setCameraError(null);
    try {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach((t) => t.stop());
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facingMode, width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setCameraActive(true);
      }
    } catch (err) {
      console.warn('Camera access error:', err);
      setCameraError('Camera access unavailable or blocked. Please use file upload.');
      setCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((t) => t.stop());
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  // Toggle Camera Facing
  const toggleFacingMode = () => {
    setFacingMode((prev) => (prev === 'environment' ? 'user' : 'environment'));
  };

  useEffect(() => {
    if (inputMode === 'camera') {
      startCamera();
    } else {
      stopCamera();
    }
    return () => {
      stopCamera();
    };
  }, [inputMode, facingMode]);

  // Handle Snapshot from Camera
  const captureSnapshot = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const capturedFile = new File([blob], `camera_capture_${Date.now()}.jpg`, {
          type: 'image/jpeg',
        });
        setSelectedFile(capturedFile);
        setPreviewUrl(canvas.toDataURL('image/jpeg'));
        stopCamera();
        runAnalysis(capturedFile);
      },
      'image/jpeg',
      0.9
    );
  };

  // Handle File Input Change
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (file.type.startsWith('image/')) {
        setPreviewUrl(URL.createObjectURL(file));
      } else {
        setPreviewUrl(null);
      }
      runAnalysis(file);
    }
  };

  // Handle Drag & Drop
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      if (file.type.startsWith('image/')) {
        setPreviewUrl(URL.createObjectURL(file));
      } else {
        setPreviewUrl(null);
      }
      runAnalysis(file);
    }
  };

  // Sample Documents for Demo Testing
  const handleLoadSample = (sampleType: string) => {
    let sampleText = '';
    let fileName = '';
    const profName = citizenProfile?.gender === 'female' ? 'Anita Devi' : 'Satish Kumar';
    const profState = citizenProfile?.state || 'Karnataka';

    if (sampleType === 'aadhaar') {
      sampleText = `GOVERNMENT OF INDIA\nUNIQUE IDENTIFICATION AUTHORITY OF INDIA\nName: ${profName}\nDOB: 15/08/1982\nGender: Male\nAddress: Tumakuru, ${profState} 572101\n9999 4105 7058\nMera Aadhaar, Meri Pehchan`;
      fileName = 'Aadhaar_Card_Verified.pdf';
    } else if (sampleType === 'land_record') {
      sampleText = `Government of ${profState} Revenue Department - Bhoomi Record of Rights (ROR)\nSurvey No: 42/1A\nHissa No: 2\nTotal Extent: 2.50 Acres\nPattedar / Land Owner: ${profName}\nDistrict: Tumakuru\nVerified Land Parcel Record`;
      fileName = 'Land_Record_ROR.pdf';
    } else if (sampleType === 'bank_passbook') {
      sampleText = `State Bank of India - Savings Bank Passbook\nAccount Holder: ${profName}\nA/C No: 38920192831\nIFSC Code: SBIN0001234\nBranch: Tumakuru Main\nAadhaar Seeded DBT Enabled`;
      fileName = 'Bank_Passbook_SBI.pdf';
    } else if (sampleType === 'expired_income') {
      sampleText = `Government of ${profState} Revenue Department\nIncome Certificate\nApplicant Name: ${profName}\nAnnual Household Income: ₹1,80,000\nValid Upto: 10/01/2023\nTahsildar Officer Digital Seal`;
      fileName = 'Expired_Income_Certificate.pdf';
    }

    const blob = new Blob([sampleText], { type: 'text/plain' });
    const sampleFile = new File([blob], fileName, { type: 'text/plain' });
    setSelectedFile(sampleFile);
    setPreviewUrl(null);
    runAnalysis(sampleFile);
  };

  // Core Audit Analysis Dispatcher
  const runAnalysis = async (fileToAnalyze: File) => {
    setProcessing(true);
    setProcessingStep(1);
    setErrorMessage(null);

    // Step 1: Preprocessing animation
    setTimeout(() => setProcessingStep(2), 350);
    // Step 2: OCR extraction animation
    setTimeout(() => setProcessingStep(3), 700);
    // Step 3: Deterministic Rules validation animation
    setTimeout(() => setProcessingStep(4), 1050);

    try {
      const response: KagazCheckAnalyzeResponse = await analyzeDocument(
        fileToAnalyze,
        fileToAnalyze.name,
        selectedSchemeId || undefined,
        citizenProfile
      );

      setLatestResult(response.document_result);
      if (response.scheme_readiness) {
        setSchemeReadiness(response.scheme_readiness);
      }
      setAuditHistory((prev) => [
        response.document_result,
        ...prev.filter((d) => d.document_type_code !== response.document_result.document_type_code),
      ]);
    } catch (err: unknown) {
      let msg = 'Document analysis failed. Please check backend connection.';
      if (err instanceof Error) msg = err.message;
      setErrorMessage(msg);
    } finally {
      setProcessing(false);
      setProcessingStep(0);
    }
  };

  const resetAuditor = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setLatestResult(null);
    setErrorMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (inputMode === 'camera') startCamera();
  };

  const getStatusBadge = (status: 'VALID' | 'WARNING' | 'INVALID' | 'EXPIRED') => {
    switch (status) {
      case 'VALID':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
            <span>VALID</span>
          </span>
        );
      case 'WARNING':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
            <span>WARNING</span>
          </span>
        );
      case 'EXPIRED':
      case 'INVALID':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-rose-100 text-rose-800 border border-rose-300">
            <AlertCircle className="h-3.5 w-3.5 text-rose-600" />
            <span>{status}</span>
          </span>
        );
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 text-left py-4">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200">
            <Camera className="h-3.5 w-3.5 text-emerald-600" />
            <span>Multimodal Vision Document Auditor</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
            KagazCheck Document Auditor
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Photograph identity records, land titles, and passbooks for deterministic statutory audit
          </p>
        </div>

        {/* Scheme Context Selector */}
        <div className="flex items-center gap-2 bg-slate-50 p-2 rounded-2xl border border-slate-200 w-full sm:w-auto">
          <Layers className="h-4 w-4 text-slate-500 shrink-0 ml-1" />
          <div className="space-y-0.5">
            <label className="text-[10px] font-bold text-slate-500 block uppercase">Target Scheme:</label>
            <select
              value={selectedSchemeId}
              onChange={(e) => setSelectedSchemeId(e.target.value)}
              className="text-xs font-bold text-slate-800 bg-transparent border-none focus:outline-none cursor-pointer pr-4"
            >
              <option value="pm-kisan-001">PM-KISAN (Income Support)</option>
              <option value="pmay-g-002">PMAY-G (Rural Housing)</option>
              <option value="pmmvy-003">PMMVY (Maternity Support)</option>
              <option value="pm-jay-004">Ayushman Bharat (PM-JAY)</option>
              <option value="raitha-vidya-005">Raitha Vidya Nidhi</option>
              {availableSchemes.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Citizen Privacy Assurance Banner */}
      <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200 text-emerald-950 text-xs flex items-start gap-2.5">
        <ShieldCheck className="h-4 w-4 text-emerald-700 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="font-bold">Statutory Privacy &amp; PII Protection</p>
          <p className="text-emerald-900 leading-relaxed text-[11px]">
            KagazCheck masks sensitive personal identifiers (Aadhaar UID, Bank A/C) in-memory using statutory UIDAI privacy guidelines. Raw images are processed temporarily without permanent server storage.
          </p>
        </div>
      </div>

      {/* Quick Demo Test Samples Banner */}
      <div className="bg-slate-100/80 p-4 rounded-2xl border border-slate-200 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
            Quick Demo Document Samples:
          </span>
          <span className="text-[10px] text-slate-500">Tap to audit instantly</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => handleLoadSample('aadhaar')}
            disabled={processing}
            className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:border-emerald-500 hover:bg-emerald-50 text-slate-700 transition cursor-pointer shadow-2xs"
          >
            📄 Aadhaar Card (Valid)
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample('land_record')}
            disabled={processing}
            className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:border-emerald-500 hover:bg-emerald-50 text-slate-700 transition cursor-pointer shadow-2xs"
          >
            🌾 Land Record (RoR / Khasra)
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample('bank_passbook')}
            disabled={processing}
            className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:border-emerald-500 hover:bg-emerald-50 text-slate-700 transition cursor-pointer shadow-2xs"
          >
            🏦 Bank Passbook (SBI IFSC)
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample('expired_income')}
            disabled={processing}
            className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-white border border-rose-200 hover:border-rose-500 hover:bg-rose-50 text-rose-800 transition cursor-pointer shadow-2xs"
          >
            ⚠️ Expired Certificate (Demo)
          </button>
        </div>
      </div>

      {/* Main Audit Studio Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Capture & Ingestion */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-5">
            {/* Mode Switcher Buttons */}
            <div className="flex p-1 bg-slate-100 rounded-2xl">
              <button
                type="button"
                onClick={() => setInputMode('camera')}
                className={`flex-1 py-2 text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 transition cursor-pointer ${
                  inputMode === 'camera'
                    ? 'bg-white text-emerald-800 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Camera className="h-3.5 w-3.5" />
                <span>Live Camera</span>
              </button>
              <button
                type="button"
                onClick={() => setInputMode('upload')}
                className={`flex-1 py-2 text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 transition cursor-pointer ${
                  inputMode === 'upload'
                    ? 'bg-white text-emerald-800 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <UploadCloud className="h-3.5 w-3.5" />
                <span>Upload File / PDF</span>
              </button>
            </div>

            {/* CAMERA CAPTURE VIEW */}
            {inputMode === 'camera' && (
              <div className="space-y-4">
                <div className="relative rounded-2xl overflow-hidden bg-slate-950 aspect-4/3 flex items-center justify-center border border-slate-800">
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                  />
                  <canvas ref={canvasRef} className="hidden" />

                  {/* Document Alignment Frame Overlay */}
                  <div className="absolute inset-4 border-2 border-dashed border-emerald-400/70 rounded-xl pointer-events-none flex flex-col justify-between p-3">
                    <div className="flex justify-between items-start">
                      <span className="text-[10px] bg-black/60 text-emerald-300 font-mono px-2 py-0.5 rounded">
                        KagazCheck Viewfinder
                      </span>
                      <button
                        type="button"
                        onClick={toggleFacingMode}
                        className="pointer-events-auto p-1.5 rounded-lg bg-black/60 text-white hover:bg-black/80 transition"
                        title="Switch Front/Back Camera"
                      >
                        <RefreshCw className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <span className="text-[10px] text-center text-white/90 bg-black/50 py-1 rounded">
                      Fit document borders inside frame
                    </span>
                  </div>

                  {cameraError && (
                    <div className="absolute inset-0 bg-slate-900/90 p-6 flex flex-col items-center justify-center text-center text-white space-y-2">
                      <AlertCircle className="h-8 w-8 text-rose-400" />
                      <p className="text-xs">{cameraError}</p>
                      <button
                        type="button"
                        onClick={() => setInputMode('upload')}
                        className="text-xs bg-emerald-600 text-white px-3 py-1.5 rounded-xl font-bold mt-2"
                      >
                        Switch to File Upload
                      </button>
                    </div>
                  )}
                </div>

                {cameraActive && (
                  <button
                    type="button"
                    onClick={captureSnapshot}
                    disabled={processing}
                    className="w-full py-3.5 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-sm shadow-sm transition flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <Camera className="h-4 w-4" />
                    <span>Capture &amp; Audit Document</span>
                  </button>
                )}
              </div>
            )}

            {/* FILE UPLOAD VIEW */}
            {inputMode === 'upload' && (
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 hover:border-emerald-500 bg-slate-50 hover:bg-emerald-50/30 rounded-2xl p-8 text-center cursor-pointer transition space-y-3"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp,application/pdf,.txt"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                <div className="h-12 w-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
                  <UploadCloud className="h-6 w-6" />
                </div>

                <div className="space-y-1">
                  <p className="text-xs font-bold text-slate-800">
                    Click to browse or drag &amp; drop document
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Supports Photos (JPEG, PNG, WebP) and PDF certificates (Max 10MB)
                  </p>
                </div>

                {selectedFile && (
                  <div className="p-2.5 bg-white rounded-xl border border-slate-200 text-xs font-medium text-slate-700 flex items-center justify-between">
                    <span className="truncate max-w-[200px]">{selectedFile.name}</span>
                    <span className="text-[10px] text-slate-500">
                      {Math.round(selectedFile.size / 1024)} KB
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Preview Thumbnail if available */}
            {previewUrl && (
              <div className="relative rounded-xl overflow-hidden border border-slate-200 aspect-16/9 bg-slate-100 flex items-center justify-center">
                <img src={previewUrl} alt="Captured Document" className="w-full h-full object-contain" />
                <button
                  type="button"
                  onClick={resetAuditor}
                  className="absolute top-2 right-2 p-1.5 rounded-full bg-black/60 text-white hover:bg-black/80 transition"
                  title="Remove image"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            )}

            {/* Active Processing Step Pipeline */}
            {processing && (
              <div className="p-5 rounded-2xl bg-emerald-50/80 border border-emerald-200 space-y-3">
                <div className="flex items-center gap-2 text-emerald-950 font-bold text-xs">
                  <Sparkles className="h-4 w-4 text-emerald-600 animate-spin" />
                  <span>Multimodal Document Processing...</span>
                </div>

                <div className="space-y-2 text-[11px]">
                  <div
                    className={`flex items-center gap-2 ${
                      processingStep >= 1 ? 'text-emerald-800 font-semibold' : 'text-slate-400'
                    }`}
                  >
                    <div
                      className={`h-2 w-2 rounded-full ${
                        processingStep >= 1 ? 'bg-emerald-600' : 'bg-slate-300'
                      }`}
                    />
                    <span>1. Image Quality &amp; Sharpness Analysis</span>
                  </div>

                  <div
                    className={`flex items-center gap-2 ${
                      processingStep >= 2 ? 'text-emerald-800 font-semibold' : 'text-slate-400'
                    }`}
                  >
                    <div
                      className={`h-2 w-2 rounded-full ${
                        processingStep >= 2 ? 'bg-emerald-600' : 'bg-slate-300'
                      }`}
                    />
                    <span>2. Multimodal OCR &amp; Field Extraction</span>
                  </div>

                  <div
                    className={`flex items-center gap-2 ${
                      processingStep >= 3 ? 'text-emerald-800 font-semibold' : 'text-slate-400'
                    }`}
                  >
                    <div
                      className={`h-2 w-2 rounded-full ${
                        processingStep >= 3 ? 'bg-emerald-600' : 'bg-slate-300'
                      }`}
                    />
                    <span>3. Deterministic Verhoeff &amp; Statutory Validation</span>
                  </div>

                  <div
                    className={`flex items-center gap-2 ${
                      processingStep >= 4 ? 'text-emerald-800 font-semibold' : 'text-slate-400'
                    }`}
                  >
                    <div
                      className={`h-2 w-2 rounded-full ${
                        processingStep >= 4 ? 'bg-emerald-600' : 'bg-slate-300'
                      }`}
                    />
                    <span>4. Citizen Profile &amp; Scheme Readiness Synthesis</span>
                  </div>
                </div>
              </div>
            )}

            {errorMessage && (
              <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-start gap-2.5">
                <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold">Audit Error</p>
                  <p className="mt-0.5">{errorMessage}</p>
                </div>
              </div>
            )}

            {/* Session Audited Documents Pills */}
            {auditHistory.length > 0 && (
              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-bold text-slate-700 uppercase tracking-wider">
                    Audited in this Session ({auditHistory.length}):
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">In-Memory Cache</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {auditHistory.map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setLatestResult(item)}
                      className={`text-[10px] font-bold px-2.5 py-1 rounded-xl border transition flex items-center gap-1 cursor-pointer ${
                        latestResult?.document_id === item.document_id
                          ? 'bg-emerald-600 text-white border-emerald-600 shadow-2xs'
                          : 'bg-white text-slate-700 border-slate-200 hover:border-emerald-500'
                      }`}
                    >
                      <span>✓ {item.document_type}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Supported Documents Quick Reference */}
          {docSpecs.length > 0 && (
            <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-xs space-y-3">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-emerald-600" />
                <span>Recognized Documents Catalog</span>
              </h4>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                {docSpecs.slice(0, 6).map((d) => (
                  <div key={d.code} className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                    <p className="font-bold text-slate-800 truncate">{d.name}</p>
                    <p className="text-[10px] text-slate-500 line-clamp-1">{d.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Audit Results & Readiness Checklist */}
        <div className="lg:col-span-7 space-y-6">
          {latestResult ? (
            <div className="space-y-6">
              {/* Top Result Card */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                  <div className="space-y-0.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      Document Audit Outcome
                    </span>
                    <h3 className="text-lg font-extrabold text-slate-900">
                      {latestResult.document_type}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    {getStatusBadge(latestResult.overall_status as any)}
                    <button
                      type="button"
                      onClick={resetAuditor}
                      className="p-1.5 rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-100 transition cursor-pointer"
                      title="Audit Another Document"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                {/* Audit Attributes Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 space-y-0.5">
                    <span className="text-[10px] font-semibold text-slate-500">Detected</span>
                    <p className="font-bold text-slate-900">
                      {latestResult.is_detected ? '✓ Yes' : '✗ Unknown'}
                    </p>
                  </div>

                  <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 space-y-0.5">
                    <span className="text-[10px] font-semibold text-slate-500">Legibility</span>
                    <p className="font-bold text-slate-900">
                      {latestResult.is_readable ? `✓ ${latestResult.image_quality_score}% Quality` : '✗ Low / Unreadable'}
                    </p>
                  </div>

                  <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 space-y-0.5">
                    <span className="text-[10px] font-semibold text-slate-500">Statutory Validity</span>
                    <p className="font-bold text-slate-900">{latestResult.validity_status}</p>
                  </div>

                  <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 space-y-0.5">
                    <span className="text-[10px] font-semibold text-slate-500">Citizen Profile</span>
                    <p className="font-bold text-slate-900">
                      {latestResult.citizen_details_match === 'MATCH'
                        ? '✓ Matched'
                        : latestResult.citizen_details_match === 'PARTIAL_MATCH'
                        ? '⚠ Partial'
                        : latestResult.citizen_details_match}
                    </p>
                  </div>
                </div>

                {/* Field-by-Field Verification Breakdown */}
                {latestResult.fields_validation.length > 0 && (
                  <div className="space-y-2.5">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Deterministic Field Verification
                    </h4>
                    <div className="space-y-2">
                      {latestResult.fields_validation.map((field, idx) => (
                        <div
                          key={idx}
                          className={`p-3 rounded-2xl border text-xs flex items-start justify-between gap-3 ${
                            field.is_valid
                              ? 'bg-emerald-50/40 border-emerald-200 text-emerald-950'
                              : 'bg-rose-50/50 border-rose-200 text-rose-950'
                          }`}
                        >
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-1.5">
                              {field.is_valid ? (
                                <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                              ) : (
                                <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
                              )}
                              <span className="font-bold">{field.label}</span>
                            </div>
                            <p className="text-[11px] text-slate-600">{field.rule_description}</p>
                            {field.issue_reason && (
                              <p className="text-[11px] font-semibold text-rose-700">
                                Issue: {field.issue_reason}
                              </p>
                            )}
                          </div>

                          {field.extracted_value && (
                            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-800 shrink-0">
                              {field.extracted_value}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Citizen Profile Match Items */}
                {latestResult.profile_match_details.length > 0 && (
                  <div className="p-3.5 rounded-2xl bg-indigo-50/50 border border-indigo-200 text-xs space-y-1.5">
                    <span className="font-bold text-indigo-950 flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                      Cross-Matching with Citizen Profile ({citizenProfile?.gender === 'female' ? 'Anita Devi' : 'Satish Kumar'}):
                    </span>
                    <ul className="space-y-1 text-[11px] text-indigo-900">
                      {latestResult.profile_match_details.map((m, idx) => (
                        <li key={idx} className="flex items-center gap-1.5">
                          <span>{m.matched ? '✓' : '✗'}</span>
                          <span>{m.details}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Actionable Next Step Banner */}
                {latestResult.recommended_action && (
                  <div className="p-4 rounded-2xl bg-slate-900 text-white text-xs flex items-center justify-between gap-3">
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                        Recommended Next Action:
                      </span>
                      <p className="text-slate-200">{latestResult.recommended_action}</p>
                    </div>
                    {schemeReadiness?.is_ready_to_apply && onApplyForScheme && (
                      <button
                        type="button"
                        onClick={() => onApplyForScheme(selectedSchemeId)}
                        className="px-3.5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold text-xs shadow-xs transition flex items-center gap-1 shrink-0 cursor-pointer"
                      >
                        <span>Proceed to Apply</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Scheme Readiness Dossier Checklist */}
              {schemeReadiness && (
                <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-xs space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                      <h4 className="font-extrabold text-sm text-slate-900">
                        {schemeReadiness.scheme_name} — Application Readiness
                      </h4>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Statutory documents required for scheme filing
                      </p>
                    </div>

                    <div className="text-right">
                      <span className="text-xs font-extrabold text-slate-800">
                        {schemeReadiness.ready_docs_count} of {schemeReadiness.total_required_docs} Ready ({schemeReadiness.readiness_percentage}%)
                      </span>
                      <div className="w-36 bg-slate-100 h-2 rounded-full mt-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            schemeReadiness.readiness_percentage === 100
                              ? 'bg-emerald-600'
                              : schemeReadiness.readiness_percentage >= 50
                              ? 'bg-amber-500'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${schemeReadiness.readiness_percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Checklist Items */}
                  <div className="space-y-2.5">
                    {schemeReadiness.checklist.map((item, idx) => (
                      <div
                        key={idx}
                        className={`p-3.5 rounded-2xl border flex items-center justify-between gap-3 ${
                          item.status === 'VALID'
                            ? 'bg-emerald-50/50 border-emerald-200'
                            : item.status === 'WARNING'
                            ? 'bg-amber-50/50 border-amber-200'
                            : 'bg-slate-50 border-slate-200'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {item.status === 'VALID' ? (
                            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
                          ) : item.status === 'WARNING' ? (
                            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
                          ) : (
                            <div className="h-5 w-5 rounded-full border-2 border-slate-300 shrink-0" />
                          )}

                          <div className="space-y-0.5">
                            <span className="text-xs font-bold text-slate-900">
                              {item.document_name}
                            </span>
                            <p className="text-[11px] text-slate-500">{item.details}</p>
                          </div>
                        </div>

                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full border shrink-0 ${
                            item.status === 'VALID'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                              : item.status === 'WARNING'
                              ? 'bg-amber-100 text-amber-800 border-amber-200'
                              : 'bg-slate-200/80 text-slate-700 border-slate-300'
                          }`}
                        >
                          {item.status}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Overall Readiness Recommendation */}
                  <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-center gap-2">
                    <Info className="h-4 w-4 text-emerald-600 shrink-0" />
                    <span>{schemeReadiness.overall_recommendation}</span>
                  </div>

                  {/* Parchaa Generation Action Button */}
                  {onGenerateParchaa && (
                    <div className="pt-2 border-t border-slate-100 flex items-center justify-end">
                      <button
                        type="button"
                        onClick={() => onGenerateParchaa(selectedSchemeId)}
                        className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow-xs transition flex items-center justify-center gap-2 cursor-pointer"
                      >
                        <FileText className="h-3.5 w-3.5 text-emerald-400" />
                        <span>Generate Application Parchaa (with Audit Readiness)</span>
                      </button>
                    </div>
                  )}
                </div>
              )}

            </div>
          ) : (
            /* Empty State */
            <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-4 shadow-xs">
              <div className="h-16 w-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto border border-emerald-200">
                <FileCheck className="h-8 w-8" />
              </div>
              <div className="space-y-1">
                <h3 className="font-extrabold text-base text-slate-900">
                  Ready for Document Ingestion &amp; Audit
                </h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                  Take a photo using the live camera on the left, upload a PDF/image, or tap one of the quick demo buttons above to see deterministic statutory verification in action.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
