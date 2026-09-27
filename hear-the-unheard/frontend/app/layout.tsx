import type { Metadata } from "next";
import { Sora, Atkinson_Hyperlegible } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
});

const atkinson = Atkinson_Hyperlegible({
  variable: "--font-atkinson",
  subsets: ["latin"],
  weight: ["400", "700"],
});

export const viewport = {
  themeColor: "#020617",
};

export const metadata: Metadata = {
  title: "Hear the Unheard - ISL & Speech Translator",
  description:
    "Breaking communication barriers by translating Indian Sign Language, speech, and text into a common understandable form.",
  manifest: "/manifest.json",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${sora.variable} ${atkinson.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col text-ink selection:bg-primary/30">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-primary focus:text-paper focus:px-4 focus:py-2 focus:rounded-md"
        >
          Skip to content
        </a>
        <header className="sticky top-0 z-40 glass-panel border-b-0 border-x-0 border-t-0 border-b border-line">
          <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3 font-display text-xl font-bold tracking-tight hover:opacity-80 transition-opacity">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg">
                <div className="w-3 h-3 rounded-full bg-white animate-pulse" />
              </div>
              <span className="text-white">Hear the <span className="text-gradient">Unheard</span></span>
            </Link>
            <nav className="flex items-center gap-2 text-sm font-semibold">
              <Link
                href="/translate"
                className="px-5 py-2.5 rounded-full text-ink-soft hover:text-white hover:bg-white/5 transition-all duration-300"
              >
                Translator
              </Link>
              <Link
                href="/about"
                className="px-5 py-2.5 rounded-full text-ink-soft hover:text-white hover:bg-white/5 transition-all duration-300"
              >
                About
              </Link>
              <Link
                href="/translate"
                className="ml-4 px-6 py-2.5 rounded-full bg-white/10 text-white border border-white/20 hover:bg-white/20 hover:scale-105 transition-all duration-300 shadow-[0_0_15px_rgba(56,189,248,0.3)] hover:shadow-[0_0_25px_rgba(192,132,252,0.5)]"
              >
                Launch App
              </Link>
            </nav>
          </div>
        </header>
        <main id="main" className="flex-1 relative z-10">
          {children}
        </main>
        <footer className="border-t border-line mt-24 glass-panel border-x-0 border-b-0 relative z-10">
          <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="text-sm text-ink-soft max-w-md">
              <strong className="text-white font-semibold">Hear the Unheard</strong>
              <br/>
              Built for real two-way communication between ISL signers and hearing/speaking people.
            </div>
            <div className="flex gap-4">
               <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-ink-soft hover:text-primary hover:bg-white/10 transition-all cursor-pointer">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
               </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
