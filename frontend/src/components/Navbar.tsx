import { useState } from 'react';
import {
  Compass,
  Search,
  BookOpen,
  User,
  FileCheck,
  Globe,
  Menu,
  X,
  ChevronDown,
  Sparkles,
  Camera,
  Mic,
} from 'lucide-react';

export type TabType = 'home' | 'find' | 'explore' | 'vanibot' | 'kagazcheck' | 'applications' | 'profile' | 'help';
export type LanguageType = 'en' | 'hi' | 'kn';

interface NavbarProps {
  currentTab: TabType;
  onTabChange: (tab: TabType) => void;
  language: LanguageType;
  onLanguageChange: (lang: LanguageType) => void;
  onOpenAssistant: () => void;
  applicationsCount?: number;
}

export function Navbar({
  currentTab,
  onTabChange,
  language,
  onLanguageChange,
  onOpenAssistant,
  applicationsCount = 2,
}: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);

  const languages: { code: LanguageType; label: string; native: string }[] = [
    { code: 'en', label: 'English', native: 'English' },
    { code: 'hi', label: 'Hindi', native: 'हिन्दी' },
    { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ' },
  ];

  const handleNav = (tab: TabType) => {
    onTabChange(tab);
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-18">
          {/* Logo & Brand */}
          <button
            onClick={() => handleNav('home')}
            className="flex items-center gap-3 text-left group focus:outline-none cursor-pointer"
          >
            <div className="h-11 w-11 rounded-2xl bg-gradient-to-tr from-emerald-800 to-emerald-600 flex items-center justify-center text-white shadow-sm shadow-emerald-200 group-hover:scale-105 transition-transform">
              <Compass className="h-6 w-6 text-emerald-100" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl text-slate-900 tracking-tight flex items-center">
                  Gram<span className="text-emerald-700">Setu</span>
                  <span className="ml-1 text-xs font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                    AI
                  </span>
                </span>
              </div>
              <p className="text-[11px] font-medium text-slate-500 hidden sm:block">
                Bridging Citizens &amp; Government Schemes
              </p>
            </div>
          </button>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1">
            <button
              onClick={() => handleNav('home')}
              className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                currentTab === 'home'
                  ? 'bg-emerald-50 text-emerald-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              Home
            </button>

            <button
              onClick={() => handleNav('find')}
              className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer ${
                currentTab === 'find'
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'text-emerald-700 hover:bg-emerald-50'
              }`}
            >
              <Search className="h-3.5 w-3.5" />
              <span>Find Schemes</span>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            </button>

            <button
              onClick={() => handleNav('explore')}
              className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer ${
                currentTab === 'explore'
                  ? 'bg-emerald-50 text-emerald-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>Explore All</span>
            </button>

            <button
              onClick={() => handleNav('vanibot')}
              className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer ${
                currentTab === 'vanibot'
                  ? 'bg-gradient-to-r from-emerald-700 to-teal-700 text-white shadow-xs'
                  : 'text-emerald-800 bg-emerald-50 hover:bg-emerald-100'
              }`}
            >
              <Mic className="h-3.5 w-3.5 text-emerald-500 animate-pulse" />
              <span>Vani-Bot</span>
              <span className="text-[9px] font-bold px-1 py-0.2 rounded bg-emerald-200 text-emerald-900">
                Voice AI
              </span>
            </button>

            <button
              onClick={() => handleNav('kagazcheck')}
              className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer ${
                currentTab === 'kagazcheck'
                  ? 'bg-emerald-50 text-emerald-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Camera className="h-3.5 w-3.5 text-emerald-600" />
              <span>KagazCheck</span>
              <span className="text-[9px] font-bold px-1 py-0.2 rounded bg-emerald-100 text-emerald-800">
                Vision
              </span>
            </button>

            <button
              onClick={() => handleNav('applications')}
              className={`px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer ${
                currentTab === 'applications'
                  ? 'bg-emerald-50 text-emerald-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <FileCheck className="h-3.5 w-3.5" />
              <span>My Applications</span>
              {applicationsCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-100 text-amber-800 font-bold">
                  {applicationsCount}
                </span>
              )}
            </button>


            <button
              onClick={() => handleNav('profile')}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer ${
                currentTab === 'profile'
                  ? 'bg-emerald-50 text-emerald-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <User className="h-3.5 w-3.5" />
              <span>My Profile</span>
            </button>
          </nav>

          {/* Right Action Tools */}
          <div className="hidden sm:flex items-center gap-3">
            {/* AI Assistant Quick Trigger */}
            <button
              onClick={onOpenAssistant}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200/80 px-3 py-2 rounded-xl transition cursor-pointer"
            >
              <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
              <span>AI Assistant</span>
            </button>

            {/* Language Selector */}
            <div className="relative">
              <button
                onClick={() => setLangDropdownOpen(!langDropdownOpen)}
                className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200/80 px-3 py-2 rounded-xl transition cursor-pointer"
              >
                <Globe className="h-3.5 w-3.5 text-slate-600" />
                <span>
                  {languages.find((l) => l.code === language)?.native || 'English'}
                </span>
                <ChevronDown className="h-3 w-3 text-slate-500" />
              </button>

              {langDropdownOpen && (
                <div className="absolute right-0 mt-1.5 w-36 bg-white rounded-xl shadow-lg border border-slate-200 py-1 z-50 animate-in fade-in zoom-in-95 duration-100">
                  {languages.map((l) => (
                    <button
                      key={l.code}
                      onClick={() => {
                        onLanguageChange(l.code);
                        setLangDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3.5 py-2 text-xs flex items-center justify-between transition-colors cursor-pointer ${
                        language === l.code
                          ? 'bg-emerald-50 text-emerald-800 font-semibold'
                          : 'text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      <span>{l.native}</span>
                      <span className="text-[10px] text-slate-400">{l.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Profile Avatar */}
            <button
              onClick={() => handleNav('profile')}
              className="h-9 w-9 rounded-full bg-slate-200 border-2 border-white shadow-xs flex items-center justify-center text-slate-700 font-semibold text-xs hover:ring-2 hover:ring-emerald-500 transition cursor-pointer"
              title="Citizen Profile"
            >
              <User className="h-4 w-4 text-slate-600" />
            </button>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex items-center gap-2 lg:hidden">
            <button
              onClick={onOpenAssistant}
              className="p-2 rounded-xl text-emerald-800 bg-emerald-50 border border-emerald-200"
              title="AI Assistant"
            >
              <Sparkles className="h-4 w-4 text-emerald-600" />
            </button>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-slate-700 bg-slate-100 hover:bg-slate-200 transition"
              aria-label="Toggle navigation"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-6 space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handleNav('home')}
              className={`p-3 rounded-xl text-xs font-semibold text-left flex items-center gap-2 ${
                currentTab === 'home' ? 'bg-emerald-50 text-emerald-800' : 'bg-slate-50 text-slate-700'
              }`}
            >
              <Compass className="h-4 w-4 text-emerald-600" />
              <span>Home</span>
            </button>

            <button
              onClick={() => handleNav('find')}
              className={`p-3 rounded-xl text-xs font-semibold text-left flex items-center gap-2 ${
                currentTab === 'find' ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-800'
              }`}
            >
              <Search className="h-4 w-4" />
              <span>Find Schemes</span>
            </button>

            <button
              onClick={() => handleNav('explore')}
              className={`p-3 rounded-xl text-xs font-semibold text-left flex items-center gap-2 ${
                currentTab === 'explore' ? 'bg-emerald-50 text-emerald-800' : 'bg-slate-50 text-slate-700'
              }`}
            >
              <BookOpen className="h-4 w-4 text-slate-600" />
              <span>Explore Schemes</span>
            </button>

            <button
              onClick={() => handleNav('vanibot')}
              className={`p-3 rounded-xl text-xs font-bold text-left flex items-center gap-2 ${
                currentTab === 'vanibot' ? 'bg-emerald-600 text-white shadow-xs' : 'bg-emerald-50 text-emerald-900 border border-emerald-200'
              }`}
            >
              <Mic className="h-4 w-4 text-emerald-500 animate-pulse" />
              <span>Vani-Bot (Voice AI)</span>
            </button>

            <button
              onClick={() => handleNav('kagazcheck')}
              className={`p-3 rounded-xl text-xs font-semibold text-left flex items-center gap-2 ${
                currentTab === 'kagazcheck' ? 'bg-emerald-50 text-emerald-800 font-bold' : 'bg-slate-50 text-slate-700'
              }`}
            >
              <Camera className="h-4 w-4 text-emerald-600" />
              <span>KagazCheck</span>
            </button>


            <button
              onClick={() => handleNav('applications')}
              className={`p-3 rounded-xl text-xs font-semibold text-left flex items-center gap-2 ${
                currentTab === 'applications' ? 'bg-emerald-50 text-emerald-800' : 'bg-slate-50 text-slate-700'
              }`}
            >
              <FileCheck className="h-4 w-4 text-slate-600" />
              <span>My Applications ({applicationsCount})</span>
            </button>
          </div>

          <button
            onClick={() => handleNav('profile')}
            className={`w-full p-3 rounded-xl text-xs font-semibold text-left flex items-center justify-between ${
              currentTab === 'profile' ? 'bg-emerald-50 text-emerald-800' : 'bg-slate-50 text-slate-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-slate-600" />
              <span>Citizen Profile</span>
            </div>
            <span className="text-[10px] text-slate-500">Edit Details</span>
          </button>

          {/* Language Selector Mobile */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">Select Language:</span>
            <div className="flex gap-1">
              {languages.map((l) => (
                <button
                  key={l.code}
                  onClick={() => onLanguageChange(l.code)}
                  className={`px-2.5 py-1 text-xs rounded-lg font-medium ${
                    language === l.code
                      ? 'bg-emerald-600 text-white font-semibold'
                      : 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {l.native}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
