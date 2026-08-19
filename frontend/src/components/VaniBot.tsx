import { useState, useEffect, useRef } from 'react';
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Sparkles,
  Send,
  Trash2,
  ExternalLink,
  ShieldCheck,
  FileCheck,
  AlertCircle,
  CheckCircle2,
  Radio,
  Keyboard,
  Info,
  ArrowRight,
  Headphones,
  FileText,
} from 'lucide-react';

import {
  transcribeAudio,
  respondVani,
  clearVaniSession,
  type CitizenProfile,
  type SchemeData,
  type SchemeMatchResult,
  type VaniSchemeCard,
  type VaniActionLink,
} from '../services/api';


export type VaniState = 'idle' | 'listening' | 'processing' | 'thinking' | 'speaking' | 'finished';

export interface VaniBotProps {
  citizenProfile?: CitizenProfile;
  activeLanguage?: string;
  onOpenSchemeModal?: (scheme: SchemeData | SchemeMatchResult | { scheme_id: string; scheme_name: string }) => void;
  onOpenKagazCheck?: (schemeId?: string) => void;
  onOpenParchaa?: (schemeId: string) => void;
}


interface ChatMessage {
  id: string;
  sender: 'citizen' | 'vani';
  text: string;
  language: string;
  audioBase64?: string | null;
  schemeCards?: VaniSchemeCard[];
  actionLinks?: VaniActionLink[];
  sources?: string[];
  suggestedFollowups?: string[];
  timestamp: string;
  isAudio?: boolean;
}

export function VaniBot({
  citizenProfile,
  activeLanguage = 'kn',
  onOpenSchemeModal,
  onOpenKagazCheck,
  onOpenParchaa,
}: VaniBotProps) {

  // Session & Language State
  const [sessionId] = useState<string>(() => `vani_session_${Date.now().toString(36)}`);
  const [language, setLanguage] = useState<string>(activeLanguage);
  
  // Voice & Processing State
  const [vaniState, setVaniState] = useState<VaniState>('idle');
  const [errorNotice, setErrorNotice] = useState<string | null>(null);
  const [keyboardMode, setKeyboardMode] = useState<boolean>(false);
  const [textInput, setTextInput] = useState<string>('');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [currentlyPlayingAudio, setCurrentlyPlayingAudio] = useState<string | null>(null);

  // Media Recording & Audio Web API Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const activeAudioElementRef = useRef<HTMLAudioElement | null>(null);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  // Available Languages
  const languages = [
    { code: 'kn', label: 'ಕನ್ನಡ (Kannada)', native: 'ಕನ್ನಡ', flag: '🇮🇳' },
    { code: 'hi', label: 'हिन्दी (Hindi)', native: 'हिन्दी', flag: '🇮🇳' },
    { code: 'en', label: 'English (Indian)', native: 'English', flag: '🌐' },
  ];

  // Conversation History
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const welcomeMessages: Record<string, string> = {
      kn: 'ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಗ್ರಾಮಸೇತು ಧ್ವನಿ ಸಹಾಯಕ (Vani-Bot). ನಿಮಗೆ ಯಾವ ಯೋಜನೆಯ ಮಾಹಿತಿ ಅಥವಾ ದಾಖಲೆಗಳ ಸಹಾಯ ಬೇಕು? ಮೈಕ್ರೊಫೋನ್ ಬಟನ್ ಒತ್ತಿ ಮಾತನಾಡಿ.',
      hi: 'नमस्ते! मैं आपका ग्रामसेतु वाणी-बॉट (Vani-Bot) हूँ। सरकारी योजनाओं की पात्रता और जरूरी दस्तावेजों के बारे में पूछने के लिए माइक दबाकर बोलें।',
      en: 'Namaste! I am Vani-Bot, your GramSetu Civic Voice Assistant. Tap the microphone and ask me anything about government schemes, eligibility, or documents.',
    };

    return [
      {
        id: 'welcome',
        sender: 'vani',
        text: welcomeMessages[activeLanguage] || welcomeMessages['kn'],
        language: activeLanguage,
        timestamp: 'Just now',
        sources: ['GramSetu Statutory Rules Engine', 'Ministry of Agriculture', 'PMAY-G Portal'],
        suggestedFollowups: activeLanguage === 'kn'
          ? [
              'ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?',
              'ನನಗೆ ಯಾವ ಯೋಜನೆ ಸಿಗುತ್ತದೆ?',
              'ಪಿಎಂ ಆವಾಸ್ ಗ್ರಾಮೀಣ ಸಹಾಯಧನ ಎಷ್ಟು?',
            ]
          : activeLanguage === 'hi'
          ? [
              'पीएम किसान के लिए कौन से दस्तावेज चाहिए?',
              'क्या मैं पीएम आवास योजना के लिए पात्र हूँ?',
              'आयुष्मान भारत 5 लाख का लाभ कैसे लें?',
            ]
          : [
              'What documents do I need for PM-KISAN?',
              'Am I eligible for PMAY-G housing?',
              'How do I apply for Raitha Vidya Nidhi?',
            ],
      },
    ];
  });

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, vaniState]);

  // Clean up recording and audio on unmount
  useEffect(() => {
    return () => {
      stopRecordingCleanup();
      stopAudioPlayback();
    };
  }, []);

  const stopAudioPlayback = () => {
    if (activeAudioElementRef.current) {
      activeAudioElementRef.current.pause();
      activeAudioElementRef.current.currentTime = 0;
      activeAudioElementRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setCurrentlyPlayingAudio(null);
    if (vaniState === 'speaking') {
      setVaniState('finished');
    }
  };

  const stopRecordingCleanup = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        console.warn('Error stopping media recorder', e);
      }
    }
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try {
        audioContextRef.current.close();
      } catch (e) {
        // ignore
      }
      audioContextRef.current = null;
    }
    setAudioLevel(0);
  };

  // Play assistant voice audio
  const playAudioResponse = (audioBase64?: string | null, text?: string, langCode: string = language) => {
    if (isMuted) return;
    stopAudioPlayback();

    if (audioBase64) {
      try {
        const audioSrc = `data:audio/mp3;base64,${audioBase64}`;
        const audio = new Audio(audioSrc);
        activeAudioElementRef.current = audio;
        setCurrentlyPlayingAudio(audioBase64);
        setVaniState('speaking');

        audio.onended = () => {
          setCurrentlyPlayingAudio(null);
          setVaniState('finished');
          activeAudioElementRef.current = null;
        };

        audio.onerror = () => {
          console.warn('Audio playback failed, falling back to Web Speech API');
          fallbackWebSpeech(text, langCode);
        };

        audio.play().catch((err) => {
          console.warn('Autoplay prevented by browser:', err);
          setCurrentlyPlayingAudio(null);
          setVaniState('finished');
        });
      } catch (err) {
        fallbackWebSpeech(text, langCode);
      }
    } else if (text) {
      fallbackWebSpeech(text, langCode);
    }
  };

  const fallbackWebSpeech = (text?: string, langCode: string = 'kn') => {
    if (!text || !('speechSynthesis' in window) || isMuted) {
      setVaniState('finished');
      return;
    }
    try {
      const cleanText = text.replace(/[*#`]/g, '').trim();
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = langCode === 'kn' ? 'kn-IN' : langCode === 'hi' ? 'hi-IN' : 'en-IN';
      utterance.rate = 0.95;
      
      utterance.onstart = () => {
        setVaniState('speaking');
        setCurrentlyPlayingAudio('browser_speech');
      };

      utterance.onend = () => {
        setCurrentlyPlayingAudio(null);
        setVaniState('finished');
      };

      utterance.onerror = () => {
        setCurrentlyPlayingAudio(null);
        setVaniState('finished');
      };

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      setVaniState('finished');
    }
  };

  // Start Voice Microphone Recording
  const startRecording = async () => {
    stopAudioPlayback();
    setErrorNotice(null);
    audioChunksRef.current = [];

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Microphone access is not supported on this browser.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Set up real-time audio visualizer analyser
      try {
        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        audioContextRef.current = audioCtx;
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        source.connect(analyser);
        analyserRef.current = analyser;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const updateVisualizer = () => {
          if (!analyserRef.current) return;
          analyserRef.current.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
          }
          const avg = sum / bufferLength;
          setAudioLevel(Math.min(100, Math.round((avg / 128) * 100)));
          animFrameRef.current = requestAnimationFrame(updateVisualizer);
        };
        updateVisualizer();
      } catch (e) {
        console.warn('AudioContext visualization setup note:', e);
      }

      // Check supported MIME type
      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
        mimeType = 'audio/ogg';
      }

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        await handleAudioCaptured(audioBlob);
      };

      mediaRecorder.start(250); // Capture chunks every 250ms
      setVaniState('listening');
    } catch (err: any) {
      console.error('Microphone capture error:', err);
      let msg = 'Could not access microphone. Please grant permission or use keyboard mode.';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        msg = 'Microphone permission denied. Please allow microphone access in your browser settings.';
      }
      setErrorNotice(msg);
      setVaniState('idle');
    }
  };

  // Stop Recording and Process Audio
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      setVaniState('processing');
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
      mediaRecorderRef.current.stop();
    }
  };

  // Handle Captured Audio Blob
  const handleAudioCaptured = async (audioBlob: Blob) => {
    setVaniState('processing');
    setErrorNotice(null);

    try {
      // Step 1: Transcribe via STT
      const transResult = await transcribeAudio(audioBlob, language);
      const userTranscript = transResult.transcript?.trim();

      if (!userTranscript) {
        setErrorNotice(
          language === 'kn'
            ? 'ಧ್ವನಿ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಮಾತನಾಡಿ.'
            : language === 'hi'
            ? 'आवाज स्पष्ट नहीं सुनाई दी। कृपया पुनः बोलें।'
            : 'Could not capture clear speech. Please try speaking again.'
        );
        setVaniState('idle');
        return;
      }

      // Add citizen voice message to chat
      const citizenMsg: ChatMessage = {
        id: `user_${Date.now()}`,
        sender: 'citizen',
        text: userTranscript,
        language: transResult.detected_language || language,
        timestamp: 'Just now',
        isAudio: true,
      };
      setMessages((prev) => [...prev, citizenMsg]);

      // Step 2: Send query to Civic Conversation Engine
      setVaniState('thinking');
      await executeCivicResponse(userTranscript, transResult.detected_language || language);
    } catch (err: any) {
      console.error('Audio processing turn error:', err);
      setErrorNotice('Error processing voice query. Please try again.');
      setVaniState('idle');
    }
  };

  // Execute Text Query Turn (used by typing, suggested prompts, and voice transcription)
  const executeCivicResponse = async (queryText: string, langToUse: string = language) => {
    setVaniState('thinking');
    setErrorNotice(null);

    try {
      const response = await respondVani({
        query: queryText,
        language: langToUse,
        session_id: sessionId,
        citizen_profile: citizenProfile,
        include_audio: true,
      });

      const vaniMsg: ChatMessage = {
        id: `vani_${Date.now()}`,
        sender: 'vani',
        text: response.reply_text,
        language: response.language,
        audioBase64: response.reply_audio_base64,
        schemeCards: response.scheme_cards,
        actionLinks: response.action_links,
        sources: response.sources,
        suggestedFollowups: response.suggested_followups,
        timestamp: 'Just now',
      };

      setMessages((prev) => [...prev, vaniMsg]);

      // Auto-play audio response
      if (response.reply_audio_base64) {
        playAudioResponse(response.reply_audio_base64, response.reply_text, response.language);
      } else {
        playAudioResponse(null, response.reply_text, response.language);
      }
    } catch (err: any) {
      console.error('Failed to get Vani-Bot civic response:', err);
      setErrorNotice('Connection error while contacting GramSetu civic engine.');
      setVaniState('idle');
    }
  };

  // Submit Typed Text Query
  const handleSendText = async () => {
    if (!textInput.trim() || vaniState === 'listening' || vaniState === 'processing') return;
    const query = textInput.trim();
    setTextInput('');

    const citizenMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: 'citizen',
      text: query,
      language: language,
      timestamp: 'Just now',
      isAudio: false,
    };
    setMessages((prev) => [...prev, citizenMsg]);

    await executeCivicResponse(query, language);
  };

  // Handle Suggested Prompt Click
  const handleSelectPrompt = async (promptText: string) => {
    if (vaniState === 'listening' || vaniState === 'processing') return;

    const citizenMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: 'citizen',
      text: promptText,
      language: language,
      timestamp: 'Just now',
      isAudio: false,
    };
    setMessages((prev) => [...prev, citizenMsg]);

    await executeCivicResponse(promptText, language);
  };

  // Reset Session History
  const handleClearChat = async () => {
    stopAudioPlayback();
    try {
      await clearVaniSession(sessionId);
    } catch (e) {
      // ignore
    }
    setMessages([
      {
        id: `welcome_${Date.now()}`,
        sender: 'vani',
        text:
          language === 'kn'
            ? 'ಸಂಭಾಷಣೆಯನ್ನು ತೆರವುಗೊಳಿಸಲಾಗಿದೆ. ನೀವು ಹೊಸ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಬಹುದು.'
            : language === 'hi'
            ? 'बातचीत रीसेट हो गई है। आप नया प्रश्न पूछ सकते हैं।'
            : 'Conversation cleared. You can ask a new question.',
        language: language,
        timestamp: 'Just now',
        suggestedFollowups: [
          'What documents do I need for PM-KISAN?',
          'Am I eligible for PMAY-G housing?',
          'What health benefits does PM-JAY offer?',
        ],
      },
    ]);
    setVaniState('idle');
  };

  // Helper labels for visual states
  const getStatusBadge = () => {
    switch (vaniState) {
      case 'listening':
        return (
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-100 text-rose-900 text-xs font-bold animate-pulse border border-rose-200">
            <Radio className="h-3.5 w-3.5 text-rose-600 animate-spin" />
            <span>Listening to Citizen... (ನಾನು ಕೇಳಿಸಿಕೊಳ್ಳುತ್ತಿದ್ದೇನೆ)</span>
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-bold border border-amber-200">
            <Sparkles className="h-3.5 w-3.5 text-amber-600 animate-spin" />
            <span>Processing Audio / STT (ಧ್ವನಿಯನ್ನು ಪರಿವರ್ತಿಸಲಾಗುತ್ತಿದೆ)</span>
          </span>
        );
      case 'thinking':
        return (
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-blue-900 text-xs font-bold border border-blue-200">
            <Sparkles className="h-3.5 w-3.5 text-blue-600 animate-spin" />
            <span>Evaluating Scheme Rules (ಅರ್ಹತೆ ಪರಿಶೀಲನೆ)</span>
          </span>
        );
      case 'speaking':
        return (
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 text-xs font-bold border border-emerald-200">
            <Volume2 className="h-3.5 w-3.5 text-emerald-600 animate-bounce" />
            <span>Speaking Response (ಉತ್ತರ ಹೇಳಲಾಗುತ್ತಿದೆ)</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold border border-slate-200">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
            <span>Ready / ಮೈಕ್ ಒತ್ತಿ ಮಾತನಾಡಿ</span>
          </span>
        );
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-gradient-to-br from-emerald-800 via-emerald-700 to-teal-900 text-white rounded-3xl p-6 sm:p-8 shadow-lg relative overflow-hidden">
        {/* Subtle Background Pattern */}
        <div className="absolute right-0 top-0 translate-x-8 -translate-y-8 w-72 h-72 rounded-full bg-white/5 blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-600/60 backdrop-blur-xs text-emerald-100 text-xs font-semibold border border-emerald-400/30">
              <Headphones className="h-3.5 w-3.5" />
              <span>Vani-Bot • Multilingual Conversational Voice Engine</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              ಗ್ರಾಮಸೇತು ಧ್ವನಿ ಸಹಾಯಕ (Vani-Bot)
            </h1>
            <p className="text-emerald-100/90 text-xs sm:text-sm max-w-xl">
              Speak naturally in Kannada, Hindi, or English. Get instant grounded answers for government scheme rules, required certificates, and application steps.
            </p>
          </div>

          {/* Language Selector & Mute Toggle */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="bg-emerald-950/60 p-1.5 rounded-2xl border border-emerald-600/40 flex items-center gap-1">
              {languages.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLanguage(l.code)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    language === l.code
                      ? 'bg-white text-emerald-900 shadow-xs'
                      : 'text-emerald-100 hover:text-white hover:bg-white/10'
                  }`}
                >
                  <span className="mr-1">{l.flag}</span>
                  <span>{l.native}</span>
                </button>
              ))}
            </div>

            {/* Audio Mute Toggle */}
            <button
              onClick={() => {
                if (!isMuted) stopAudioPlayback();
                setIsMuted(!isMuted);
              }}
              title={isMuted ? 'Unmute voice playback' : 'Mute voice playback'}
              className={`p-2.5 rounded-2xl border transition cursor-pointer ${
                isMuted
                  ? 'bg-rose-500/20 border-rose-400/40 text-rose-200'
                  : 'bg-emerald-950/60 border-emerald-600/40 text-emerald-100 hover:bg-emerald-900/80'
              }`}
            >
              {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
            </button>

            {/* Clear History */}
            <button
              onClick={handleClearChat}
              title="Clear conversation session"
              className="p-2.5 rounded-2xl bg-emerald-950/60 border border-emerald-600/40 text-emerald-100 hover:bg-emerald-900/80 hover:text-white transition cursor-pointer"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Interactive Voice Deck */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Big Microphone Command Center */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-6 text-center">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Voice Interface
            </span>
            {getStatusBadge()}
          </div>

          {/* Big Circular Microphone Interaction Button */}
          <div className="py-6 flex flex-col items-center justify-center relative">
            {/* Live Audio Activity Pulsating Rings */}
            {vaniState === 'listening' && (
              <div
                className="absolute rounded-full bg-rose-500/20 animate-ping pointer-events-none transition-all duration-75"
                style={{
                  width: `${140 + audioLevel * 1.2}px`,
                  height: `${140 + audioLevel * 1.2}px`,
                }}
              />
            )}

            {vaniState === 'speaking' && (
              <div className="absolute rounded-full bg-emerald-500/20 animate-pulse w-48 h-48 pointer-events-none" />
            )}

            <button
              onClick={() => {
                if (vaniState === 'listening') {
                  stopRecording();
                } else if (vaniState === 'speaking') {
                  stopAudioPlayback();
                } else {
                  startRecording();
                }
              }}
              className={`relative z-10 w-32 h-32 rounded-full flex flex-col items-center justify-center text-white transition-all shadow-xl cursor-pointer ${
                vaniState === 'listening'
                  ? 'bg-rose-600 hover:bg-rose-700 ring-8 ring-rose-200 scale-105 animate-pulse'
                  : vaniState === 'processing' || vaniState === 'thinking'
                  ? 'bg-amber-500 ring-8 ring-amber-100 opacity-90'
                  : vaniState === 'speaking'
                  ? 'bg-emerald-600 ring-8 ring-emerald-100 hover:bg-emerald-700'
                  : 'bg-gradient-to-tr from-emerald-700 to-emerald-500 hover:scale-105 ring-8 ring-emerald-50'
              }`}
            >
              {vaniState === 'listening' ? (
                <>
                  <MicOff className="h-10 w-10 text-white" />
                  <span className="text-[11px] font-extrabold mt-1">STOP</span>
                </>
              ) : vaniState === 'speaking' ? (
                <>
                  <VolumeX className="h-10 w-10 text-white" />
                  <span className="text-[11px] font-extrabold mt-1">STOP VOICE</span>
                </>
              ) : (
                <>
                  <Mic className="h-10 w-10 text-white" />
                  <span className="text-[11px] font-extrabold mt-1">TAP TO SPEAK</span>
                </>
              )}
            </button>
          </div>

          {/* Live Waveform Activity Meter */}
          {vaniState === 'listening' ? (
            <div className="space-y-2">
              <div className="flex items-center justify-center gap-1 h-8">
                {[...Array(12)].map((_, i) => (
                  <div
                    key={i}
                    className="w-1.5 bg-rose-500 rounded-full transition-all duration-75"
                    style={{
                      height: `${Math.max(6, Math.sin((i + audioLevel) * 0.5) * audioLevel * 0.4 + 10)}px`,
                    }}
                  />
                ))}
              </div>
              <p className="text-xs font-semibold text-rose-700">
                Listening... Tap STOP when done speaking
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              <h3 className="font-bold text-sm text-slate-800">
                {language === 'kn'
                  ? 'ಮಾತನಾಡಲು ಬಟನ್ ಒತ್ತಿರಿ'
                  : language === 'hi'
                  ? 'बोलने के लिए बटन दबाएं'
                  : 'Tap the Button to Speak'}
              </h3>
              <p className="text-xs text-slate-500 max-w-xs mx-auto">
                {language === 'kn'
                  ? 'ನಿಮ್ಮ ಸ್ವಂತ ಭಾಷೆಯಲ್ಲಿ ಯೋಜನೆ, ಅರ್ಹತೆ ಅಥವಾ ದಾಖಲೆಗಳ ಬಗ್ಗೆ ಕೇಳಿ.'
                  : language === 'hi'
                  ? 'अपनी भाषा में सरकारी योजनाओं और आवश्यक दस्तावेजों के बारे में पूछें।'
                  : 'Ask about any central or state welfare scheme in your regional dialect.'}
              </p>
            </div>
          )}

          {/* Error Alert Display */}
          {errorNotice && (
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5 text-left">
              <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">{errorNotice}</p>
              </div>
            </div>
          )}

          {/* Mode Switcher: Voice vs Type */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
            <button
              onClick={() => setKeyboardMode(!keyboardMode)}
              className="text-xs font-medium text-slate-600 hover:text-emerald-700 flex items-center gap-1.5 cursor-pointer"
            >
              <Keyboard className="h-3.5 w-3.5" />
              <span>{keyboardMode ? 'Hide Type Input' : 'Type inquiry instead'}</span>
            </button>

            <span className="text-[11px] text-slate-400">
              Privacy First • Zero Storage
            </span>
          </div>

          {/* Keyboard Input Box (If enabled) */}
          {keyboardMode && (
            <div className="flex items-center gap-2 pt-2 animate-in fade-in duration-150">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendText()}
                placeholder={
                  language === 'kn'
                    ? 'ಇಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ...'
                    : language === 'hi'
                    ? 'यहाँ लिखें...'
                    : 'Type scheme question here...'
                }
                className="flex-1 text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
              />
              <button
                onClick={handleSendText}
                disabled={!textInput.trim() || vaniState === 'listening'}
                className="p-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-40 transition cursor-pointer"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Multi-Turn Conversation Flow & Grounded Scheme Cards */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200 shadow-xs flex flex-col h-[640px] overflow-hidden">
          {/* Conversation Header */}
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-bold text-xs text-slate-800">
                Conversational Dialogue Feed
              </span>
            </div>

            <div className="text-[11px] font-medium text-slate-500 flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              <span>Grounded Scheme Intelligence</span>
            </div>
          </div>

          {/* Chat Messages Body */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 bg-slate-50/40">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.sender === 'citizen' ? 'justify-end' : 'justify-start'}`}
              >
                {/* Assistant Avatar */}
                {msg.sender === 'vani' && (
                  <div className="h-8 w-8 rounded-2xl bg-emerald-700 text-white flex items-center justify-center shrink-0 font-bold text-xs shadow-xs">
                    V
                  </div>
                )}

                <div
                  className={`max-w-[88%] rounded-3xl p-4 sm:p-5 text-xs leading-relaxed space-y-3 shadow-2xs ${
                    msg.sender === 'citizen'
                      ? 'bg-emerald-700 text-white rounded-br-xs'
                      : 'bg-white text-slate-800 border border-slate-200 rounded-bl-xs'
                  }`}
                >
                  {/* Message Sender Header */}
                  <div className="flex items-center justify-between text-[11px] opacity-80 border-b border-black/5 pb-1.5">
                    <span className="font-bold">
                      {msg.sender === 'citizen' ? 'Citizen (ನೀವು)' : 'Vani-Bot Assistant'}
                    </span>
                    <span className="text-[10px]">{msg.timestamp}</span>
                  </div>

                  {/* Message Text Content */}
                  <div className="whitespace-pre-line text-xs font-normal">
                    {msg.text}
                  </div>

                  {/* Audio Playback Controls on Assistant Message */}
                  {msg.sender === 'vani' && (
                    <div className="pt-2 border-t border-slate-100 flex items-center gap-2">
                      <button
                        onClick={() => playAudioResponse(msg.audioBase64, msg.text, msg.language)}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                          currentlyPlayingAudio === msg.audioBase64
                            ? 'bg-emerald-600 text-white'
                            : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
                        }`}
                      >
                        <Volume2 className="h-3.5 w-3.5" />
                        <span>
                          {currentlyPlayingAudio === msg.audioBase64 ? 'Playing...' : 'Play Voice'}
                        </span>
                      </button>

                      {currentlyPlayingAudio === msg.audioBase64 && (
                        <button
                          onClick={stopAudioPlayback}
                          className="px-2.5 py-1.5 rounded-xl text-xs font-medium bg-rose-50 text-rose-700 hover:bg-rose-100 transition cursor-pointer"
                        >
                          Stop
                        </button>
                      )}
                    </div>
                  )}

                  {/* Matched Scheme Cards */}
                  {msg.schemeCards && msg.schemeCards.length > 0 && (
                    <div className="space-y-2 pt-2">
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 block">
                        Verified Scheme Matches:
                      </span>
                      {msg.schemeCards.map((sc) => (
                        <div
                          key={sc.scheme_id}
                          className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-slate-800 space-y-2"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <h4 className="font-bold text-xs text-slate-900">
                                {sc.scheme_name}
                              </h4>
                              {sc.category && (
                                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                                  {sc.category}
                                </span>
                              )}
                            </div>
                            {sc.eligible_status === true && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-600 text-white shrink-0">
                                Eligible (ಅರ್ಹ)
                              </span>
                            )}
                          </div>

                          {/* Key benefits preview */}
                          {sc.key_benefits.length > 0 && (
                            <div className="text-[11px] text-slate-600 space-y-0.5">
                              <span className="font-semibold text-slate-700">Entitlement: </span>
                              <span>{sc.key_benefits[0]}</span>
                            </div>
                          )}

                          {/* Quick Actions */}
                          <div className="flex flex-wrap items-center gap-2 pt-1">
                            {onOpenKagazCheck && (
                              <button
                                onClick={() => onOpenKagazCheck(sc.scheme_id)}
                                className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-100 hover:bg-emerald-200 px-2.5 py-1 rounded-lg transition cursor-pointer"
                              >
                                <FileCheck className="h-3 w-3" />
                                <span>Audit in KagazCheck</span>
                              </button>
                            )}

                            {onOpenParchaa && (
                              <button
                                onClick={() => onOpenParchaa(sc.scheme_id)}
                                className="inline-flex items-center gap-1 text-[11px] font-bold text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-300 px-2.5 py-1 rounded-lg transition cursor-pointer"
                              >
                                <FileText className="h-3 w-3 text-emerald-700" />
                                <span>Generate Parchaa</span>
                              </button>
                            )}

                            {onOpenSchemeModal && (
                              <button
                                onClick={() => onOpenSchemeModal({
                                  scheme_id: sc.scheme_id,
                                  scheme_name: sc.scheme_name,
                                })}
                                className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-700 hover:text-slate-900 bg-white border border-slate-200 px-2.5 py-1 rounded-lg transition cursor-pointer"
                              >
                                <span>View Details</span>
                                <ArrowRight className="h-3 w-3" />
                              </button>
                            )}


                            {sc.official_url && (
                              <a
                                href={sc.official_url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-slate-700 px-1 py-1"
                              >
                                <ExternalLink className="h-3 w-3" />
                                <span>Portal</span>
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Sources Footnote */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="pt-2 border-t border-black/5 flex items-center gap-1.5 text-[10px] text-slate-400">
                      <Info className="h-3 w-3 text-emerald-600" />
                      <span>Verified: {msg.sources.join(', ')}</span>
                    </div>
                  )}

                  {/* Suggested Followups */}
                  {msg.suggestedFollowups && msg.suggestedFollowups.length > 0 && (
                    <div className="space-y-1.5 pt-2">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        Tap to Speak / Ask:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.suggestedFollowups.map((fUp, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSelectPrompt(fUp)}
                            className="text-[11px] px-2.5 py-1 rounded-xl bg-slate-100 hover:bg-emerald-50 hover:text-emerald-900 text-slate-700 text-left transition border border-slate-200/60 cursor-pointer"
                          >
                            {fUp}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={chatBottomRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
