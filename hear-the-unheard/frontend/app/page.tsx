import Link from "next/link";

function HandSignIcon() {
  return (
    <svg viewBox="0 0 64 64" className="w-14 h-14" fill="none" aria-hidden="true">
      <path
        d="M20 34V16a4 4 0 0 1 8 0v12M28 28V12a4 4 0 0 1 8 0v16M36 28V14a4 4 0 0 1 8 0v18M44 32v-8a4 4 0 0 1 8 0v14c0 8-6 14-14 14h-4c-6 0-9-2-13-6l-8-9a4 4 0 0 1 6-5l5 4"
        stroke="url(#hand-gradient)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <defs>
        <linearGradient id="hand-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="var(--color-primary)" />
          <stop offset="100%" stopColor="var(--color-accent)" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function SpeechIcon() {
  return (
    <svg viewBox="0 0 64 64" className="w-14 h-14" fill="none" aria-hidden="true">
      <path
        d="M12 20a6 6 0 0 1 6-6h28a6 6 0 0 1 6 6v16a6 6 0 0 1-6 6H30l-10 8v-8h-2a6 6 0 0 1-6-6V20Z"
        stroke="url(#speech-gradient)"
        strokeWidth="3"
        strokeLinejoin="round"
      />
      <path d="M22 24h20M22 30h14" stroke="url(#speech-gradient)" strokeWidth="3" strokeLinecap="round" />
      <defs>
        <linearGradient id="speech-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="var(--color-accent)" />
          <stop offset="100%" stopColor="var(--color-primary)" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export default function Home() {
  return (
    <div className="relative overflow-hidden">
      {/* Decorative background blobs */}
      <div className="absolute top-20 -left-64 w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px] mix-blend-screen pointer-events-none" />
      <div className="absolute top-40 -right-64 w-[600px] h-[600px] bg-accent/20 rounded-full blur-[120px] mix-blend-screen pointer-events-none" />

      {/* Hero Section */}
      <section className="relative max-w-7xl mx-auto px-6 pt-32 pb-32">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="relative z-10 animate-float" style={{ animationDuration: '8s' }}>
            <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full glass-panel mb-8 border-white/10 shadow-lg">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-accent"></span>
              </span>
              <span className="text-xs font-bold uppercase tracking-widest text-ink">
                Real-time ISL translation live
              </span>
            </div>
            
            <h1 className="font-display text-6xl md:text-7xl lg:text-[5rem] font-extrabold leading-[1.05] tracking-tight">
              Signed. Spoken.<br />
              <span className="text-gradient drop-shadow-sm">Understood.</span>
            </h1>
            
            <p className="mt-8 text-xl leading-relaxed max-w-lg text-ink-soft font-medium">
              Hear the Unheard turns Indian Sign Language into text and
              speech in real time — and turns speech back into something a
              signer can read. One conversation, both directions.
            </p>
            
            <div className="mt-12 flex flex-wrap items-center gap-6">
              <Link
                href="/translate"
                className="group relative inline-flex items-center justify-center rounded-full bg-white text-paper px-8 py-4 text-lg font-bold hover:bg-gray-100 transition-all duration-300 shadow-[0_0_20px_rgba(255,255,255,0.3)] hover:shadow-[0_0_30px_rgba(255,255,255,0.5)] hover:scale-105"
              >
                Start Translating
                <svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
              </Link>
              <Link href="/about" className="text-lg font-semibold text-ink-soft hover:text-white transition-colors flex items-center gap-2">
                See how it works
              </Link>
            </div>
          </div>

          {/* Interactive Flow Diagram */}
          <div className="relative z-10 glass-panel rounded-3xl p-10 shadow-2xl border-white/10 hover:border-white/20 transition-all duration-500 group overflow-hidden">
             {/* Shimmer effect */}
             <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/5 to-transparent group-hover:animate-[shimmer_2s_infinite]" />
             
            <div className="flex items-center justify-between relative z-10">
              <div className="flex flex-col items-center gap-4 w-28 transform transition-transform group-hover:scale-105">
                <div className="w-20 h-20 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10 shadow-[0_0_15px_rgba(56,189,248,0.2)]">
                  <HandSignIcon />
                </div>
                <span className="text-sm text-ink-soft text-center font-medium">Signer performs<br /><strong className="text-white mt-1 block">"NAME WHAT"</strong></span>
              </div>
              
              <div className="flex-1 flex flex-col items-center px-4 relative">
                <div className="w-full h-1 bg-white/10 rounded-full relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-primary to-accent w-full origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1000 ease-out" />
                </div>
                <div className="mt-4 px-3 py-1 rounded-full bg-accent/20 border border-accent/30 text-xs font-bold text-accent tracking-wider uppercase">
                  Recognized Live
                </div>
              </div>
              
              <div className="flex flex-col items-center gap-4 w-28 transform transition-transform group-hover:scale-105 delay-100">
                <div className="w-20 h-20 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10 shadow-[0_0_15px_rgba(192,132,252,0.2)]">
                  <SpeechIcon />
                </div>
                <span className="text-sm text-ink-soft text-center font-medium">Heard as<br /><strong className="text-white mt-1 block">"What's your name?"</strong></span>
              </div>
            </div>
            
            <div className="mt-10 p-4 rounded-xl bg-white/5 border border-white/10 relative z-10">
              <p className="text-sm text-ink-soft text-center font-medium">
                The same pipeline runs the other way — speech becomes text the signer can read, live.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 pb-32">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl md:text-4xl font-bold">Breaking the <span className="text-gradient">barrier.</span></h2>
          <p className="mt-4 text-ink-soft text-lg max-w-2xl mx-auto">Seamless two-way communication powered by real-time computer vision and speech recognition.</p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              title: "ISL to Text & Speech",
              desc: "A webcam reads hand and body movement. Recognized signs are assembled into a real sentence, not a word-by-word gloss.",
              icon: "M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            },
            {
              title: "Speech to Text",
              desc: "A hearing person speaks normally. Their words appear as clear, readable text for the signer, instantly transcribed.",
              icon: "M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            },
            {
              title: "Built to Grow",
              desc: "The vocabulary and recognition model expand without changing the app — see the current coverage on the translator page.",
              icon: "M13 10V3L4 14h7v7l9-11h-7z"
            }
          ].map((feature, i) => (
            <div key={i} className="glass-panel rounded-2xl p-8 hover:-translate-y-2 transition-transform duration-300 border-white/5 hover:border-white/20 group">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={feature.icon} />
                </svg>
              </div>
              <h3 className="font-display text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-ink-soft leading-relaxed font-medium">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes shimmer {
          100% { transform: translateX(100%); }
        }
      `}} />
    </div>
  );
}
