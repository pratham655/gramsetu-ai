import { useEffect, useState } from 'react';
import { Navbar, type TabType, type LanguageType } from './components/Navbar';
import { Footer } from './components/Footer';
import { Hero } from './components/Hero';
import { HowItWorks } from './components/HowItWorks';
import { PopularSchemes } from './components/PopularSchemes';
import { ProfileForm } from './components/ProfileForm';
import { MatchResults } from './components/MatchResults';
import { SchemeDetailsModal } from './components/SchemeDetailsModal';
import { MyProfileView } from './components/MyProfileView';
import { MyApplicationsView, type ApplicationRecord } from './components/MyApplicationsView';
import { AssistantPanel } from './components/AssistantPanel';
import {
  fetchActiveSchemes,
  matchEligibility,
  type CitizenProfile,
  type EligibilityMatchResponse,
  type SchemeData,
  type SchemeMatchResult,
} from './services/api';
import { Search, Sparkles, BookOpen, AlertCircle } from 'lucide-react';

export default function App() {
  const [currentTab, setCurrentTab] = useState<TabType>('home');
  const [language, setLanguage] = useState<LanguageType>('en');

  // Citizen Profile State
  const [profile, setProfile] = useState<CitizenProfile>({
    age: 42,
    income: 180000,
    state: 'Karnataka',
    district: 'Tumakuru',
    gender: 'male',
    occupation: 'farmer',
    landholding: 2.5,
    category: 'OBC',
    bpl: true,
  });

  // Schemes from PostgreSQL Database
  const [schemes, setSchemes] = useState<SchemeData[]>([]);
  const [loadingSchemes, setLoadingSchemes] = useState<boolean>(true);

  // YojanaMatch State
  const [matching, setMatching] = useState<boolean>(false);
  const [matchResponse, setMatchResponse] = useState<EligibilityMatchResponse | null>(null);
  const [matchError, setMatchError] = useState<string | null>(null);

  // Scheme Details Modal State
  const [selectedScheme, setSelectedScheme] = useState<SchemeData | SchemeMatchResult | null>(null);

  // Assistant Drawer State
  const [assistantOpen, setAssistantOpen] = useState<boolean>(false);

  // Application Dossiers Tracking State
  const [applications, setApplications] = useState<ApplicationRecord[]>([
    {
      id: 'app-1',
      schemeId: 'pm-kisan-001',
      schemeName: 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
      category: 'Agriculture',
      status: 'Ready to Apply',
      documentsTotal: 4,
      documentsReady: 4,
      lastUpdated: 'Today',
      nextAction: 'Submit Aadhaar & Land RoR on pmkisan.gov.in or at nearest CSC Kendra',
      officialUrl: 'https://pmkisan.gov.in',
      requiredDocuments: [
        'Aadhaar Card',
        'Proof of Agricultural Land Ownership (ROR / Khasra)',
        'Aadhaar-seeded Bank Passbook',
        'Mobile Number linked with Aadhaar',
      ],
    },
    {
      id: 'app-2',
      schemeId: 'pmay-g-002',
      schemeName: 'Pradhan Mantri Awas Yojana - Gramin (PMAY-G)',
      category: 'Housing & Rural Development',
      status: 'Documents Required',
      documentsTotal: 5,
      documentsReady: 3,
      lastUpdated: 'Yesterday',
      nextAction: 'Verify SECC / BPL list enrollment at Gram Panchayat office',
      officialUrl: 'https://pmayg.nic.in',
      requiredDocuments: [
        'Aadhaar Card',
        'BPL Ration Card / SECC 2011 Verification Document',
        'Bank Account Passbook (Aadhaar linked)',
        'Homestead Land Ownership / Allotment Order',
        'MGNREGA Job Card',
      ],
    },
  ]);

  // Load Database Schemes on Mount
  useEffect(() => {
    async function loadSchemes() {
      try {
        setLoadingSchemes(true);
        const data = await fetchActiveSchemes();
        setSchemes(data);
      } catch (err) {
        console.error('Failed to fetch schemes:', err);
      } finally {
        setLoadingSchemes(false);
      }
    }
    loadSchemes();
  }, []);

  // Handle Eligibility Matching Request
  const handleRunMatch = async (profileToMatch: CitizenProfile) => {
    setProfile(profileToMatch);
    setMatching(true);
    setMatchError(null);
    setCurrentTab('find');
    try {
      const response = await matchEligibility(profileToMatch);
      setMatchResponse(response);
    } catch (err: unknown) {
      let msg = 'Failed to evaluate eligibility. Please check backend connection.';
      if (err instanceof Error) msg = err.message;
      setMatchError(msg);
    } finally {
      setMatching(false);
    }
  };

  // Add Scheme to Applications Dossier
  const handleStartApplication = (scheme: SchemeData | SchemeMatchResult) => {
    const sId = 'id' in scheme ? scheme.id : scheme.scheme_id;
    const sName = 'name' in scheme ? scheme.name : scheme.scheme_name;
    const sCat = ('category' in scheme && scheme.category) ? scheme.category : 'General Welfare';
    const sDocs = scheme.required_documents || [];
    const sUrl = scheme.official_source_url;

    // Check if already in applications
    const exists = applications.find((a) => a.schemeId === sId);
    if (!exists) {
      const newApp: ApplicationRecord = {
        id: `app-${Date.now()}`,
        schemeId: sId,
        schemeName: sName,
        category: sCat,
        status: 'Preparing',
        documentsTotal: sDocs.length,
        documentsReady: 1,
        lastUpdated: 'Just now',
        nextAction: 'Audit required certificates and verify at Gram Panchayat',
        officialUrl: sUrl,
        requiredDocuments: sDocs,
      };
      setApplications((prev) => [newApp, ...prev]);
    }
    setCurrentTab('applications');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col justify-between selection:bg-emerald-100 selection:text-emerald-900 font-sans">
      {/* Production Header Navigation */}
      <Navbar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        language={language}
        onLanguageChange={setLanguage}
        onOpenAssistant={() => setAssistantOpen(true)}
        applicationsCount={applications.length}
      />

      {/* Main Content Area */}
      <main className="flex-1 w-full">
        {/* VIEW 1: HOME PAGE */}
        {currentTab === 'home' && (
          <div>
            <Hero
              onFindSchemes={() => {
                setCurrentTab('find');
                if (!matchResponse) handleRunMatch(profile);
              }}
              onExploreSchemes={() => setCurrentTab('explore')}
            />

            <HowItWorks />

            <PopularSchemes
              schemes={schemes}
              loading={loadingSchemes}
              onViewDetails={(s) => setSelectedScheme(s)}
              onCheckEligibility={() => {
                setCurrentTab('find');
                if (!matchResponse) handleRunMatch(profile);
              }}
            />
          </div>
        )}

        {/* VIEW 2: FIND SCHEMES & MATCH RESULTS */}
        {currentTab === 'find' && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              {/* Left Column: Form Questionnaire */}
              <div className="lg:col-span-5">
                <ProfileForm
                  initialProfile={profile}
                  onSubmit={handleRunMatch}
                  loading={matching}
                />
              </div>

              {/* Right Column: Matched Schemes */}
              <div className="lg:col-span-7">
                {matchError && (
                  <div className="p-5 rounded-3xl bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-bold">Eligibility Match Error</p>
                      <p className="mt-1">{matchError}</p>
                    </div>
                  </div>
                )}

                {matching ? (
                  <div className="bg-white rounded-3xl border border-slate-200 p-16 text-center space-y-4 shadow-xs">
                    <div className="h-12 w-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto border border-emerald-200">
                      <Sparkles className="h-6 w-6 animate-spin" />
                    </div>
                    <div className="space-y-1">
                      <h3 className="font-bold text-base text-slate-900">
                        Evaluating Eligibility Rules...
                      </h3>
                      <p className="text-xs text-slate-500 max-w-sm mx-auto">
                        Comparing your profile parameters against statutory central and state scheme guidelines.
                      </p>
                    </div>
                  </div>
                ) : matchResponse ? (
                  <MatchResults
                    matchData={matchResponse}
                    onViewDetails={(s) => setSelectedScheme(s)}
                    onEditProfile={() => {
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                  />
                ) : (
                  <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-4 shadow-xs">
                    <Search className="h-10 w-10 text-emerald-600 mx-auto" />
                    <div className="space-y-1">
                      <h3 className="font-bold text-base text-slate-900">
                        Ready to Find Your Eligible Schemes
                      </h3>
                      <p className="text-xs text-slate-500 max-w-md mx-auto">
                        Fill in your profile details on the left and tap "Find My Eligible Schemes"
                        to view instant, deterministic rule breakdowns.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* VIEW 3: EXPLORE ALL SCHEMES */}
        {currentTab === 'explore' && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
            <div className="text-left space-y-2 border-b border-slate-200 pb-6">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200">
                <BookOpen className="h-3.5 w-3.5 text-emerald-600" />
                <span>Verified Schemes Repository</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Explore Government Schemes
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 max-w-2xl">
                Browse official central and state welfare initiatives with statutory criteria,
                benefit entitlements, and required application documents.
              </p>
            </div>

            <PopularSchemes
              schemes={schemes}
              loading={loadingSchemes}
              onViewDetails={(s) => setSelectedScheme(s)}
              onCheckEligibility={() => {
                setCurrentTab('find');
                if (!matchResponse) handleRunMatch(profile);
              }}
            />
          </div>
        )}

        {/* VIEW 4: MY PROFILE */}
        {currentTab === 'profile' && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <MyProfileView
              profile={profile}
              onSaveProfile={(newProf) => setProfile(newProf)}
              onFindSchemes={(prof) => handleRunMatch(prof)}
            />
          </div>
        )}

        {/* VIEW 5: MY APPLICATIONS */}
        {currentTab === 'applications' && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <MyApplicationsView
              applications={applications}
              onExploreSchemes={() => setCurrentTab('explore')}
            />
          </div>
        )}
      </main>

      {/* Scheme Details Modal */}
      <SchemeDetailsModal
        scheme={selectedScheme}
        onClose={() => setSelectedScheme(null)}
        onStartApplication={handleStartApplication}
      />

      {/* Grounded AI Assistant Drawer */}
      <AssistantPanel
        isOpen={assistantOpen}
        onClose={() => setAssistantOpen(false)}
        citizenProfile={profile}
      />

      {/* Production Footer */}
      <Footer onNavigateTab={(tab) => setCurrentTab(tab)} />
    </div>
  );
}
