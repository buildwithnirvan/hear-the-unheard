"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE_URL, WS_RECOGNIZE_URL } from "@/lib/config";
import type { RecognizeWsMessage, RecognizedToken } from "@/lib/recognizeTypes";

const CAPTURE_FPS = 8;

type ConnectionState = "idle" | "connecting" | "connected" | "error" | "closed";

interface HistoryEntry {
  id: string;
  sender: "Signer" | "Speaker";
  text: string;
  rawGlosses?: string[];
  timestamp: string;
}

const SUPPORTED_LANGUAGES = [
  { code: "en-IN", name: "English (India)" },
  { code: "hi-IN", name: "Hindi (हिंदी)" },
  { code: "ta-IN", name: "Tamil (தமிழ்)" },
  { code: "te-IN", name: "Telugu (తెలుగు)" },
  { code: "mr-IN", name: "Marathi (मराठी)" },
  { code: "bn-IN", name: "Bengali (বাংলা)" },
];

export default function TranslatePage() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [selectedLang, setSelectedLang] = useState("en-IN");
  const [smartAiMode, setSmartAiMode] = useState(true);

  const addHistory = (sender: "Signer" | "Speaker", text: string, rawGlosses?: string[]) => {
    if (!text.trim()) return;
    const entry: HistoryEntry = {
      id: Math.random().toString(36).substring(2, 9),
      sender,
      text,
      rawGlosses,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
    };
    setHistory((prev) => [entry, ...prev]);
  };

  const exportHistoryTxt = () => {
    if (history.length === 0) return;
    const content = history
      .map((h) => `[${h.timestamp}] ${h.sender}: ${h.text}${h.rawGlosses ? ` (Glosses: ${h.rawGlosses.join(" ")})` : ""}`)
      .join("\n");
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ISL_Translation_Transcript_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportHistoryJson = () => {
    if (history.length === 0) return;
    const blob = new Blob([JSON.stringify(history, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ISL_Translation_Transcript_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      {/* Top Header & Settings bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10 pb-6 border-b border-line">
        <div>
          <span className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-accent bg-accent/10 px-3 py-1 rounded-full mb-3 border border-accent/20">
            Bidirectional AI Studio
          </span>
          <h1 className="font-display text-4xl font-extrabold text-white">Live Translator</h1>
          <p className="text-ink-soft mt-2 text-base max-w-xl">
            Real-time Indian Sign Language recognition paired with multilingual speech transcription.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4 glass-panel p-4 rounded-2xl border-white/10">
          <div>
            <label className="block text-xs font-bold text-ink-soft uppercase tracking-wider mb-1">Target Speech Language</label>
            <select
              value={selectedLang}
              onChange={(e) => setSelectedLang(e.target.value)}
              className="bg-white/5 border border-white/10 text-white rounded-xl px-3 py-2 text-sm font-semibold focus:outline-none focus:border-accent"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code} className="bg-slate-900 text-white">
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3 pt-4 md:pt-0">
            <button
              onClick={() => setSmartAiMode(!smartAiMode)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                smartAiMode
                  ? "bg-accent/20 border-accent text-accent shadow-[0_0_15px_rgba(192,132,252,0.3)]"
                  : "bg-white/5 border-white/10 text-ink-soft hover:text-white"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${smartAiMode ? "bg-accent animate-ping" : "bg-ink-soft"}`} />
              {smartAiMode ? "AI Grammar Smoothing ON" : "Raw Gloss Mode"}
            </button>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-8 items-start mb-12">
        <SigningPanel onTranslated={(text, glosses) => addHistory("Signer", text, glosses)} selectedLang={selectedLang} smartAiMode={smartAiMode} />
        <SpeakingPanel onSpoken={(text) => addHistory("Speaker", text)} selectedLang={selectedLang} />
      </div>

      {/* Transcript & History Section */}
      <section className="glass-panel rounded-3xl p-8 border-white/10 shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6 border-b border-line pb-4">
          <div>
            <h2 className="font-display text-2xl font-bold text-white flex items-center gap-3">
              <span>📋 Live Conversation Transcript</span>
              <span className="text-xs px-2.5 py-1 rounded-full bg-primary/20 text-primary border border-primary/30 font-semibold">
                {history.length} messages
              </span>
            </h2>
          </div>
          <div className="flex gap-3">
            <button
              onClick={exportHistoryTxt}
              disabled={history.length === 0}
              className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold text-white hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              📄 Export TXT
            </button>
            <button
              onClick={exportHistoryJson}
              disabled={history.length === 0}
              className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold text-white hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              💾 Export JSON
            </button>
            <button
              onClick={() => setHistory([])}
              disabled={history.length === 0}
              className="px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-sm font-semibold text-red-400 hover:bg-red-500/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              Clear Log
            </button>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="py-12 text-center text-ink-soft">
            <p className="text-base">No transcript log yet. Start signing or speaking above to build your conversation history.</p>
          </div>
        ) : (
          <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
            {history.map((entry) => (
              <div
                key={entry.id}
                className={`p-4 rounded-2xl border transition-all ${
                  entry.sender === "Signer"
                    ? "bg-primary/10 border-primary/20 ml-0 mr-12"
                    : "bg-accent/10 border-accent/20 ml-12 mr-0"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs font-bold uppercase tracking-wider ${entry.sender === "Signer" ? "text-primary-light" : "text-accent"}`}>
                    {entry.sender === "Signer" ? "🤟 Signer (ISL)" : "🎙 Speaker (Voice/Text)"}
                  </span>
                  <span className="text-xs text-ink-soft">{entry.timestamp}</span>
                </div>
                <p className="text-white text-base font-medium">{entry.text}</p>
                {entry.rawGlosses && entry.rawGlosses.length > 0 && (
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-xs text-ink-soft font-mono">Glosses:</span>
                    <div className="flex flex-wrap gap-1">
                      {entry.rawGlosses.map((g, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-white/5 border border-white/10 text-accent font-mono">
                          {g}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

/* ----------------------------- Signing panel ----------------------------- */

function SigningPanel({
  onTranslated,
  selectedLang,
  smartAiMode,
}: {
  onTranslated: (text: string, glosses: string[]) => void;
  selectedLang: string;
  smartAiMode: boolean;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const captureTimerRef = useRef<number | null>(null);

  const [cameraOn, setCameraOn] = useState(false);
  const [connection, setConnection] = useState<ConnectionState>("idle");
  const [poseDetected, setPoseDetected] = useState(false);
  const [tokens, setTokens] = useState<RecognizedToken[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sentence, setSentence] = useState<string | null>(null);
  const [translating, setTranslating] = useState(false);

  const stopCapture = useCallback(() => {
    if (captureTimerRef.current !== null) {
      window.clearInterval(captureTimerRef.current);
      captureTimerRef.current = null;
    }
  }, []);

  const stopCamera = useCallback(() => {
    stopCapture();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    wsRef.current?.close();
    wsRef.current = null;
    setCameraOn(false);
    setConnection("idle");
    setPoseDetected(false);
  }, [stopCapture]);

  const handleMessage = useCallback((raw: MessageEvent) => {
    let msg: RecognizeWsMessage;
    try {
      msg = JSON.parse(raw.data);
    } catch {
      return;
    }
    if (msg.type === "status") {
      setPoseDetected(msg.pose_present);
    } else if (msg.type === "recognition") {
      setTokens((prev) => [...prev, { gloss: msg.gloss, confidence: msg.confidence, at: Date.now() }]);
    } else if (msg.type === "error") {
      setErrorMsg(msg.detail);
    }
  }, []);

  const startCamera = useCallback(async () => {
    setErrorMsg(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraOn(true);
    } catch {
      setErrorMsg("Couldn't access the camera. Check your browser's camera permission for this site and try again.");
      return;
    }

    setConnection("connecting");
    const ws = new WebSocket(WS_RECOGNIZE_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnection("connected");
      const canvas = canvasRef.current;
      const video = videoRef.current;
      if (!canvas || !video) return;

      captureTimerRef.current = window.setInterval(() => {
        if (ws.readyState !== WebSocket.OPEN || video.videoWidth === 0) return;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(
          (blob) => {
            if (blob && ws.readyState === WebSocket.OPEN) ws.send(blob);
          },
          "image/jpeg",
          0.8
        );
      }, 1000 / CAPTURE_FPS);
    };

    ws.onmessage = handleMessage;
    ws.onerror = () => {
      setConnection("error");
      setErrorMsg("Couldn't reach recognition server at " + WS_RECOGNIZE_URL);
    };
    ws.onclose = () => {
      setConnection("closed");
      stopCapture();
    };
  }, [handleMessage, stopCapture]);

  useEffect(() => stopCamera, [stopCamera]);

  const translateNow = useCallback(async () => {
    if (tokens.length === 0) return;
    setTranslating(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tokens: tokens.map((t) => t.gloss) }),
      });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const data = await res.json();
      
      let finalSentence = data.sentence;
      if (smartAiMode && finalSentence) {
        // AI Formatting polish
        finalSentence = finalSentence.charAt(0).toUpperCase() + finalSentence.slice(1);
        if (!/[.!?]$/.test(finalSentence)) finalSentence += ".";
      }
      
      setSentence(finalSentence);
      onTranslated(finalSentence, tokens.map((t) => t.gloss));
    } catch {
      setErrorMsg("Couldn't reach translation service.");
    } finally {
      setTranslating(false);
    }
  }, [tokens, smartAiMode, onTranslated]);

  const speak = useCallback(() => {
    if (!sentence || typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const utterance = new SpeechSynthesisUtterance(sentence);
    utterance.lang = selectedLang;
    window.speechSynthesis.speak(utterance);
  }, [sentence, selectedLang]);

  const clearAll = useCallback(() => {
    setTokens([]);
    setSentence(null);
    setErrorMsg(null);
  }, []);

  return (
    <section className="glass-panel rounded-3xl p-8 border-white/10 shadow-xl" aria-labelledby="signing-heading">
      <div className="flex items-center justify-between mb-6">
        <h2 id="signing-heading" className="font-display text-xl font-bold text-white flex items-center gap-2">
          <span>🤟 ISL Sign Input</span>
        </h2>
        <StatusDot
          label={
            !cameraOn
              ? "Camera Off"
              : connection === "connected"
              ? poseDetected
                ? "Person Detected"
                : "No Person in Frame"
              : connection === "connecting"
              ? "Connecting…"
              : connection === "error"
              ? "Connection Error"
              : "Disconnected"
          }
          active={cameraOn && connection === "connected" && poseDetected}
          warning={connection === "error"}
        />
      </div>

      <div className="relative aspect-video bg-black/40 rounded-2xl overflow-hidden mb-6 border border-white/10 shadow-inner">
        <video ref={videoRef} muted playsInline className="w-full h-full object-cover [transform:scaleX(-1)]" aria-label="Live camera preview" />
        {!cameraOn && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-ink-soft gap-3">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
              <svg className="w-8 h-8 text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <span className="text-sm font-medium">Click "Start Camera" to perform ISL signs</span>
          </div>
        )}
        <canvas ref={canvasRef} className="hidden" />
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        {!cameraOn ? (
          <button
            onClick={startCamera}
            className="rounded-xl bg-gradient-to-r from-primary to-accent text-white px-6 py-3 text-sm font-bold hover:opacity-90 transition-all shadow-lg hover:scale-105"
          >
            Start Camera
          </button>
        ) : (
          <button
            onClick={stopCamera}
            className="rounded-xl border border-white/10 bg-white/5 text-white px-6 py-3 text-sm font-bold hover:bg-white/10 transition-all"
          >
            Stop Camera
          </button>
        )}
        <button
          onClick={translateNow}
          disabled={tokens.length === 0 || translating}
          className="rounded-xl bg-white text-paper px-6 py-3 text-sm font-bold hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:scale-105"
        >
          {translating ? "Translating…" : "Translate Signs"}
        </button>
        <button
          onClick={clearAll}
          disabled={tokens.length === 0 && !sentence}
          className="rounded-xl border border-white/10 bg-white/5 text-white px-6 py-3 text-sm font-bold hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          Clear
        </button>
      </div>

      {errorMsg && (
        <p role="alert" className="text-sm text-red-300 bg-red-950/40 border border-red-500/30 rounded-xl p-4 mb-6">
          {errorMsg}
        </p>
      )}

      <div className="space-y-6">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-ink-soft mb-3">Recognized Sign Glosses</h3>
          {tokens.length === 0 ? (
            <p className="text-sm text-ink-soft italic">No signs recognized yet. Perform signs in camera view.</p>
          ) : (
            <ul className="flex flex-wrap gap-2">
              {tokens.map((t, i) => (
                <li key={i} className="rounded-xl bg-accent/20 border border-accent/40 text-accent px-4 py-1.5 text-sm font-bold shadow-sm" title={`Confidence: ${(t.confidence * 100).toFixed(0)}%`}>
                  {t.gloss}
                </li>
              ))}
            </ul>
          )}
        </div>

        {sentence !== null && (
          <div className="border-t border-line pt-6">
            <h3 className="text-xs font-bold uppercase tracking-wider text-ink-soft mb-2">Generated Translation</h3>
            <p className="text-2xl font-semibold text-white leading-relaxed">{sentence || "(empty)"}</p>
            <button onClick={speak} className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary/20 border border-primary/30 text-primary-light text-sm font-bold hover:bg-primary/30 transition-all">
              🔊 Speak Aloud ({selectedLang})
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

/* ----------------------------- Speaking panel ----------------------------- */

type SpeechRecognitionResultLike = { transcript: string };
type SpeechRecognitionEventLike = {
  resultIndex: number;
  results: { [i: number]: { 0: SpeechRecognitionResultLike; isFinal: boolean }; length: number };
};
interface SpeechRecognitionLike extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onresult: ((ev: SpeechRecognitionEventLike) => void) | null;
  onerror: ((ev: unknown) => void) | null;
  onend: (() => void) | null;
}

function getSpeechRecognitionCtor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

function SpeakingPanel({
  onSpoken,
  selectedLang,
}: {
  onSpoken: (text: string) => void;
  selectedLang: string;
}) {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interim, setInterim] = useState("");
  const [typed, setTyped] = useState("");
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    setSupported(getSpeechRecognitionCtor() !== null);
  }, []);

  const startListening = useCallback(() => {
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) return;
    const recognition = new Ctor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = selectedLang;

    recognition.onresult = (ev) => {
      let finalText = "";
      let interimText = "";
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        const result = ev.results[i];
        if (result.isFinal) {
          finalText += result[0].transcript;
          onSpoken(result[0].transcript.trim());
        } else {
          interimText += result[0].transcript;
        }
      }
      if (finalText) setTranscript((prev) => (prev ? prev + " " + finalText.trim() : finalText.trim()));
      setInterim(interimText);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, [selectedLang, onSpoken]);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
    setInterim("");
  }, []);

  const handleSendTyped = () => {
    if (!typed.trim()) return;
    onSpoken(typed.trim());
    setTranscript((prev) => (prev ? prev + " " + typed.trim() : typed.trim()));
    setTyped("");
  };

  const clearAll = useCallback(() => {
    setTranscript("");
    setInterim("");
    setTyped("");
  }, []);

  const displayText = transcript + (interim ? (transcript ? " " : "") + interim : "");

  return (
    <section className="glass-panel rounded-3xl p-8 border-white/10 shadow-xl" aria-labelledby="speaking-heading">
      <div className="flex items-center justify-between mb-6">
        <h2 id="speaking-heading" className="font-display text-xl font-bold text-white flex items-center gap-2">
          <span>🎙 Speech & Text Input</span>
        </h2>
        <StatusDot label={listening ? "Listening..." : "Idle"} active={listening} />
      </div>

      {!supported && (
        <p className="text-sm text-amber-300 bg-amber-950/40 border border-amber-500/30 rounded-xl p-4 mb-6">
          Speech recognition is unsupported in this browser. Type your message below — it will be converted into readable text for the signer.
        </p>
      )}

      <div className="flex flex-wrap gap-3 mb-6">
        {supported &&
          (!listening ? (
            <button
              onClick={startListening}
              className="rounded-xl bg-gradient-to-r from-accent to-primary text-white px-6 py-3 text-sm font-bold hover:opacity-90 transition-all shadow-lg hover:scale-105"
            >
              Start Listening
            </button>
          ) : (
            <button
              onClick={stopListening}
              className="rounded-xl border border-white/10 bg-white/5 text-white px-6 py-3 text-sm font-bold hover:bg-white/10 transition-all animate-pulse"
            >
              Stop Listening
            </button>
          ))}
        <button
          onClick={clearAll}
          disabled={!transcript && !typed}
          className="rounded-xl border border-white/10 bg-white/5 text-white px-6 py-3 text-sm font-bold hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          Clear
        </button>
      </div>

      <div className="min-h-[160px] rounded-2xl bg-black/40 border border-white/10 p-6 mb-6 flex flex-col justify-between">
        <div aria-live="polite" className="text-2xl leading-relaxed font-semibold text-white">
          {displayText || <span className="text-ink-soft text-lg font-normal">Spoken words appear here live in large text for signers to read...</span>}
        </div>
        <div className="text-xs text-ink-soft mt-4 flex justify-between border-t border-white/5 pt-3">
          <span>Active Language: <strong>{selectedLang}</strong></span>
          <span>Live Display</span>
        </div>
      </div>

      <div className="space-y-3">
        <label htmlFor="typed-message" className="text-xs font-bold uppercase tracking-wider text-ink-soft block">
          Or Type Message for Signer
        </label>
        <div className="flex gap-3">
          <input
            id="typed-message"
            type="text"
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendTyped()}
            placeholder="Type a message and press Enter..."
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-ink-soft focus:outline-none focus:border-accent text-sm font-medium"
          />
          <button
            onClick={handleSendTyped}
            disabled={!typed.trim()}
            className="px-6 py-3 rounded-xl bg-white/10 border border-white/20 text-white font-bold text-sm hover:bg-white/20 disabled:opacity-40 transition-all"
          >
            Send
          </button>
        </div>
      </div>
    </section>
  );
}

function StatusDot({ label, active, warning }: { label: string; active: boolean; warning?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2 text-xs font-bold text-ink-soft">
      <span
        className={`w-2.5 h-2.5 rounded-full ${
          warning ? "bg-red-500 animate-bounce" : active ? "bg-accent shadow-[0_0_10px_#c084fc]" : "bg-white/20"
        }`}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}
