import React from 'react';
import { ShieldCheck, Lock, CheckCircle, XOctagon, FileCheck, ShieldAlert } from 'lucide-react';

/**
 * EnforcementProofPanel — Visual proof panel demonstrating runtime authorization
 * and post-execution filesystem verification for hackathon evaluation.
 */
export default function EnforcementProofPanel({ actions = [] }) {
  const safeActions = Array.isArray(actions) ? actions : [];
  const blockedCount = safeActions.filter((a) => a && a.decision === 'BLOCK').length;
  const executedCount = safeActions.filter((a) => a && a.executionStatus === 'EXECUTED').length;
  const verifiedCount = safeActions.filter((a) => a && a.verificationStatus === 'PASSED').length;

  return (
    <div className="glass-card p-4 sm:p-6 border-l-4 border-l-cyan-500 bg-gradient-to-r from-blue-950/40 via-gray-900/60 to-slate-900/40 animate-fade-in-up mb-6 shadow-xl">
      {/* Header Statement */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-4 border-b border-[var(--color-border)]">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
            <ShieldCheck size={22} className="sm:w-6 sm:h-6" />
          </div>
          <div className="min-w-0">
            <h3 className="text-xs sm:text-sm font-bold tracking-wide uppercase text-cyan-400 truncate">
              Enforced Runtime Authorization & Proof Layer
            </h3>
            <p className="text-[0.7rem] sm:text-xs text-[var(--color-text-secondary)] italic mt-0.5 leading-relaxed">
              "Our system does not merely monitor AI agents. It sits between the agent and its tools and enforces authorization at runtime."
            </p>
          </div>
        </div>

        <span className="text-[0.65rem] font-bold px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 uppercase tracking-wider flex items-center gap-1.5 shrink-0 self-start sm:self-auto">
          <CheckCircle size={12} />
          Runtime Enforced
        </span>
      </div>

      {/* Proof Stat Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        {/* Metric 1: Allowed Executed */}
        <div className="bg-[var(--color-bg-primary)] p-3.5 rounded-lg border border-emerald-500/20 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
            <FileCheck size={18} />
          </div>
          <div className="min-w-0">
            <div className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold truncate">
              Allowed Executed
            </div>
            <div className="text-base sm:text-lg font-bold text-emerald-400 font-mono">
              {executedCount} Actions
            </div>
          </div>
        </div>

        {/* Metric 2: Blocked Destructive */}
        <div className="bg-[var(--color-bg-primary)] p-3.5 rounded-lg border border-red-500/20 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400 shrink-0">
            <XOctagon size={18} />
          </div>
          <div className="min-w-0">
            <div className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold truncate">
              Blocked & Not Executed
            </div>
            <div className="text-base sm:text-lg font-bold text-red-400 font-mono">
              {blockedCount} Destructive
            </div>
          </div>
        </div>

        {/* Metric 3: Verification Proof */}
        <div className="bg-[var(--color-bg-primary)] p-3.5 rounded-lg border border-cyan-500/20 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
            <Lock size={18} />
          </div>
          <div className="min-w-0">
            <div className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold truncate">
              Filesystem Proof Status
            </div>
            <div className="text-xs font-bold text-cyan-400 font-mono truncate">
              ✓ PASSED ({verifiedCount} Verified)
            </div>
          </div>
        </div>
      </div>

      {/* Subtext */}
      <div className="mt-3 text-[0.65rem] sm:text-[0.7rem] text-[var(--color-text-muted)] flex items-start gap-2 leading-relaxed">
        <ShieldAlert size={14} className="text-amber-400 shrink-0 mt-0.5" />
        <span>
          A blocked action cannot execute because tool APIs in <code className="text-cyan-400 font-mono">backend/sandbox/</code> remain inaccessible until authorized by the Security Gateway.
        </span>
      </div>
    </div>
  );
}
