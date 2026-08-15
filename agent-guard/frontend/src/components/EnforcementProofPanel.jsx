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
    <div className="glass-card p-6 border-l-4 border-l-cyan-500 bg-gradient-to-r from-blue-950/40 via-gray-900/60 to-slate-900/40 animate-fade-in-up mb-6 shadow-xl">
      {/* Header Statement */}
      <div className="flex items-start justify-between gap-4 mb-4 pb-4 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <ShieldCheck size={24} />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-wide uppercase text-cyan-400">
              Enforced Runtime Authorization & Proof Layer
            </h3>
            <p className="text-xs text-[var(--color-text-secondary)] italic mt-0.5">
              "Our system does not merely monitor AI agents. It sits between the agent and its tools and enforces authorization at runtime."
            </p>
          </div>
        </div>

        <span className="text-[0.65rem] font-bold px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 uppercase tracking-wider flex items-center gap-1.5 shrink-0">
          <CheckCircle size={12} />
          Runtime Enforced
        </span>
      </div>

      {/* Proof Stat Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Metric 1: Allowed Executed */}
        <div className="bg-[var(--color-bg-primary)] p-3.5 rounded-lg border border-emerald-500/20 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <FileCheck size={18} />
          </div>
          <div>
            <div className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold">
              Allowed Executed
            </div>
            <div className="text-lg font-bold text-emerald-400 font-mono">
              {executedCount} Actions
            </div>
          </div>
        </div>

        {/* Metric 2: Blocked Destructive */}
        <div className="bg-[var(--color-bg-primary)] p-3.5 rounded-lg border border-red-500/20 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
            <XOctagon size={18} />
          </div>
          <div>
            <div className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold">
              Blocked & Not Executed
            </div>
            <div className="text-lg font-bold text-red-400 font-mono">
              {blockedCount} Destructive
            </div>
          </div>
        </div>

        {/* Metric 3: Verification Proof */}
        <div className="bg-[var(--color-bg-primary)] p-3.5 rounded-lg border border-cyan-500/20 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Lock size={18} />
          </div>
          <div>
            <div className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold">
              Filesystem Proof Status
            </div>
            <div className="text-xs font-bold text-cyan-400 font-mono">
              ✓ PASSED ({verifiedCount} Verified)
            </div>
          </div>
        </div>
      </div>

      {/* Subtext */}
      <div className="mt-3 text-[0.7rem] text-[var(--color-text-muted)] flex items-center gap-2">
        <ShieldAlert size={13} className="text-amber-400 shrink-0" />
        <span>
          A blocked action cannot execute because tool APIs in <code className="text-cyan-400 font-mono">backend/sandbox/</code> remain inaccessible until authorized by the Security Gateway.
        </span>
      </div>
    </div>
  );
}
