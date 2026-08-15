import React from 'react';
import { Activity } from 'lucide-react';

/**
 * AgentBehaviorSummary — Displays aggregated statistics for the agent's behavior
 * including total actions, aligned/unaligned counts, drift, cumulative risk, and safety score.
 */
export default function AgentBehaviorSummary({ summary = {} }) {
  const {
    totalActions = 0,
    aligned = 0,
    partiallyAligned = 0,
    blocked = 0,
    approvalRequired = 0,
    goalViolations = 0,
    currentDriftLevel = 'NORMAL',
    currentDriftScore = 0,
    cumulativeRiskLevel = 'LOW',
    cumulativeRiskScore = 0,
    agentSafetyScore = 100,
  } = summary;

  return (
    <div className="glass-card p-6 mb-6 border border-[var(--color-border)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border)] mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Activity size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-wide uppercase text-[var(--color-text-primary)]">
              Agent Behavior & Security Summary
            </h3>
            <p className="text-[0.7rem] text-[var(--color-text-muted)]">
              Comprehensive telemetry across runtime alignment, violations, and safety scoring
            </p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold block">
            Prototype Security Score
          </span>
          <span className={`text-base font-bold font-mono ${agentSafetyScore >= 80 ? 'text-emerald-400' : agentSafetyScore >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
            {agentSafetyScore}/100
          </span>
        </div>
      </div>

      {/* Grid of Telemetry */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-[var(--color-border)]">
          <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
            Total Proposed
          </span>
          <span className="text-lg font-bold font-mono text-slate-100">{totalActions} Actions</span>
        </div>

        <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-emerald-500/20">
          <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
            Goal Aligned
          </span>
          <span className="text-lg font-bold font-mono text-emerald-400">{aligned} Aligned</span>
        </div>

        <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-amber-500/20">
          <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
            Partially Aligned
          </span>
          <span className="text-lg font-bold font-mono text-amber-400">{partiallyAligned} Actions</span>
        </div>

        <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-red-500/20">
          <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
            Blocked & Prevented
          </span>
          <span className="text-lg font-bold font-mono text-red-400">{blocked} Blocked</span>
        </div>

        <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-blue-500/20">
          <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
            Human Approvals
          </span>
          <span className="text-lg font-bold font-mono text-blue-400">{approvalRequired} Reviews</span>
        </div>

        <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-red-500/20">
          <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
            Constraint Violations
          </span>
          <span className="text-lg font-bold font-mono text-red-400">{goalViolations} Detected</span>
        </div>

        <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-purple-500/20">
          <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
            Multi-Step Drift
          </span>
          <span className="text-lg font-bold font-mono text-purple-400">
            {currentDriftLevel} ({currentDriftScore}%)
          </span>
        </div>

        <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-pink-500/20">
          <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
            Cumulative Risk
          </span>
          <span className="text-lg font-bold font-mono text-pink-400">
            {cumulativeRiskLevel} ({cumulativeRiskScore}%)
          </span>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-[var(--color-border)] text-[0.7rem] text-[var(--color-text-muted)] flex items-center justify-between">
        <span>* Prototype Security Score derived from alignment stability, blocked actions, drift velocity, and cumulative risk.</span>
        <span className="text-cyan-400 font-mono">Continuous Verification Active</span>
      </div>
    </div>
  );
}
