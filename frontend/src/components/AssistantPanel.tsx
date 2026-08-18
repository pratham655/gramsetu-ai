import { useState } from 'react';
import {
  Sparkles,
  X,
  Send,
  User,
  Bot,
  ShieldCheck,
} from 'lucide-react';
import type { CitizenProfile } from '../services/api';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  sources?: string[];
}

interface AssistantPanelProps {
  isOpen: boolean;
  onClose: () => void;
  citizenProfile: CitizenProfile;
}

export function AssistantPanel({
  isOpen,
  onClose,
  citizenProfile,
}: AssistantPanelProps) {
  if (!isOpen) return null;

  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: `Namaste! I am your GramSetu Civic Assistant. I can help explain scheme eligibility criteria, statutory benefits, and required application documents. How can I help you today?`,
      timestamp: 'Just now',
      sources: ['National Schemes Gazette', 'Ministry of Agriculture', 'MoHFW'],
    },
  ]);

  const quickQuestions = [
    'Why am I eligible for PM-KISAN?',
    'What documents do I need for PMAY-G?',
    'What health benefits does PM-JAY offer?',
    'How do I apply for Raitha Vidya Nidhi?',
  ];

  const handleSend = (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim()) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: 'Just now',
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');

    // Generate grounded knowledge response based on verified scheme knowledge base
    setTimeout(() => {
      let reply = '';
      let sources = ['Official Scheme Guidelines'];

      const lower = text.toLowerCase();
      if (lower.includes('pm-kisan') || lower.includes('kisan') || lower.includes('farmer')) {
        reply = `Under **PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)**, eligible landholding farmer families receive ₹6,000 per year directly transferred in three equal installments of ₹2,000 into their Aadhaar-linked bank accounts. To apply, you need your Aadhaar card, Land Ownership Records (ROR/Khatauni), and bank passbook.`;
        sources = ['pmkisan.gov.in', 'Ministry of Agriculture'];
      } else if (lower.includes('pmay') || lower.includes('awas') || lower.includes('housing')) {
        reply = `**PMAY-Gramin** provides ₹1,20,000 (plain areas) or ₹1,30,000 (hilly/difficult areas) for pucca house construction to homeless or kutcha house rural households identified in SECC/BPL lists. Beneficiaries also receive 90–95 days of unskilled labour wages under MGNREGA.`;
        sources = ['pmayg.nic.in', 'Ministry of Rural Development'];
      } else if (lower.includes('jay') || lower.includes('ayushman') || lower.includes('health')) {
        reply = `**Ayushman Bharat (PM-JAY)** provides comprehensive cashless health insurance coverage up to ₹5,00,000 per family per year for secondary and tertiary care hospitalization across all empaneled hospitals in India.`;
        sources = ['nha.gov.in', 'National Health Authority'];
      } else if (lower.includes('vidya') || lower.includes('karnataka') || lower.includes('scholarship')) {
        reply = `**Karnataka Raitha Vidya Nidhi** is a Karnataka state scholarship offering ₹2,000 to ₹11,000 annually for children of registered farmers pursuing higher education (PUC, ITI, Degree, Postgraduate).`;
        sources = ['raitamitra.karnataka.gov.in', 'Karnataka Agriculture Dept'];
      } else {
        reply = `GramSetu AI evaluates your profile against statutory eligibility criteria. Based on your current profile (${citizenProfile.occupation || 'citizen'}, ${citizenProfile.state || 'India'}, ${citizenProfile.landholding !== undefined ? `${citizenProfile.landholding} acres` : 'land'}), you can view exact criteria breakdowns on the Find Schemes page.`;
        sources = ['GramSetu Statutory Rules Engine'];
      }

      const botMsg: Message = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: reply,
        timestamp: 'Just now',
        sources,
      };
      setMessages((prev) => [...prev, botMsg]);
    }, 400);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-md h-full flex flex-col shadow-2xl border-l border-slate-200 text-left">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-emerald-600 flex items-center justify-center text-white font-bold shadow-xs">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-900">GramSetu Assistant</h3>
              <p className="text-[11px] text-slate-500">Grounded Civic Intelligence</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'assistant' && (
                <div className="h-7 w-7 rounded-full bg-emerald-700 text-white flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed space-y-1.5 shadow-2xs ${
                  msg.sender === 'user'
                    ? 'bg-emerald-600 text-white rounded-br-xs'
                    : 'bg-white text-slate-800 border border-slate-200 rounded-bl-xs'
                }`}
              >
                <div className="prose prose-xs whitespace-pre-line font-normal">{msg.text}</div>

                {msg.sources && msg.sources.length > 0 && (
                  <div className="pt-1.5 border-t border-slate-100 flex flex-wrap items-center gap-1 text-[10px] text-slate-400">
                    <ShieldCheck className="h-3 w-3 text-emerald-600" />
                    <span>Sources: {msg.sources.join(', ')}</span>
                  </div>
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="h-7 w-7 rounded-full bg-slate-300 text-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Quick Suggested Prompts */}
        <div className="p-3 border-t border-slate-200 bg-white space-y-1.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Suggested Inquiries:
          </span>
          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
            {quickQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-emerald-50 hover:text-emerald-900 text-slate-700 text-left transition cursor-pointer"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Message Input Box */}
        <div className="p-3 border-t border-slate-200 bg-slate-50 flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about scheme rules, documents, or benefits..."
            className="flex-1 text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim()}
            className="p-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-40 transition cursor-pointer"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
