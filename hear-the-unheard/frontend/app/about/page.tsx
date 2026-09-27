export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <div className="text-center mb-12">
        <span className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-accent bg-accent/10 px-4 py-1.5 rounded-full border border-accent/20 mb-4">
          System Architecture & Mission
        </span>
        <h1 className="font-display text-4xl md:text-5xl font-extrabold text-white">How Hear the Unheard Works</h1>
        <p className="mt-4 text-lg text-ink-soft max-w-2xl mx-auto">
          An inside look at our real-time computer vision, pose estimation, and speech synthesis pipeline.
        </p>
      </div>

      <div className="space-y-8">
        <div className="glass-panel rounded-3xl p-8 border-white/10 shadow-xl">
          <h2 className="font-display text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <span className="w-8 h-8 rounded-xl bg-primary/20 flex items-center justify-center text-primary text-sm font-bold border border-primary/30">1</span>
            Computer Vision Landmark Pipeline
          </h2>
          <p className="text-ink-soft leading-relaxed text-base">
            Your webcam stream is captured locally and analyzed frame-by-frame. Using MediaPipe Landmark Extraction, key points across hands, arms, and shoulders are converted into normalized numeric coordinate tensors without uploading raw video streams, protecting user privacy.
          </p>
        </div>

        <div className="glass-panel rounded-3xl p-8 border-white/10 shadow-xl">
          <h2 className="font-display text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <span className="w-8 h-8 rounded-xl bg-accent/20 flex items-center justify-center text-accent text-sm font-bold border border-accent/30">2</span>
            ML Sign Recognition Engine
          </h2>
          <p className="text-ink-soft leading-relaxed text-base">
            Landmark sequences are evaluated against our custom-trained ISL Pose Classifier model. Individual signs are segmented, classified, and paired with statistical confidence scores in real-time over low-latency WebSockets.
          </p>
        </div>

        <div className="glass-panel rounded-3xl p-8 border-white/10 shadow-xl">
          <h2 className="font-display text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <span className="w-8 h-8 rounded-xl bg-gradient-to-r from-primary to-accent text-white text-sm font-bold">3</span>
            Natural Language Formatting & Speech Synthesis
          </h2>
          <p className="text-ink-soft leading-relaxed text-base">
            Isolated sign glosses are processed through grammar normalization rules to construct fluid sentences. The output is rendered in large high-contrast text and converted into vocal output using Web Speech Synthesis across multiple regional Indian languages.
          </p>
        </div>

        <div className="glass-panel rounded-3xl p-8 border-white/10 shadow-xl border-accent/30 bg-accent/5">
          <h3 className="font-display text-xl font-bold text-white mb-2">Current System Status & Coverage</h3>
          <p className="text-sm text-ink-soft leading-relaxed">
            The recognition model currently understands 76 active ISL vocabulary signs trained on authentic Indian Sign Language dataset footage. The system is designed to seamlessly scale vocabulary without requiring client-side updates.
          </p>
        </div>
      </div>
    </div>
  );
}
