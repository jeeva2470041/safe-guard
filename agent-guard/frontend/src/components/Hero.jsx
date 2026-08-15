import React from 'react';

/**
 * Hero component with modern dark theme styling, subtle neon accents,
 * and clear call-to-action buttons for portfolio showcasing.
 */
export default function Hero({
  name = "Alex Developer",
  role = "Full Stack Engineer & AI Security Specialist",
  tagline = "Architecting resilient, autonomous systems with deterministic runtime guardrails."
}) {
  return (
    <section className="relative min-h-[70vh] flex items-center justify-center bg-slate-950 text-slate-100 px-6 py-20 overflow-hidden">
      {/* Background Gradient Orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[350px] h-[350px] bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-4xl mx-auto text-center space-y-8 z-10">
        {/* Availability Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-semibold tracking-wide">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          AVAILABLE FOR NEW PROJECTS
        </div>

        {/* Headline */}
        <div className="space-y-4">
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            Hi, I'm <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">{name}</span>
          </h1>
          <p className="text-xl sm:text-2xl font-medium text-slate-300">
            {role}
          </p>
          <p className="max-w-2xl mx-auto text-sm sm:text-base text-slate-400 leading-relaxed">
            {tagline}
          </p>
        </div>

        {/* CTA Actions */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <a
            href="#projects"
            className="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-all shadow-lg shadow-blue-600/25 hover:shadow-blue-600/40"
          >
            View Projects →
          </a>
          <a
            href="#contact"
            className="px-6 py-3 rounded-lg border border-slate-700 hover:border-slate-500 bg-slate-900/60 hover:bg-slate-800 text-slate-200 text-sm font-semibold transition-all"
          >
            Get In Touch
          </a>
        </div>
      </div>
    </section>
  );
}
