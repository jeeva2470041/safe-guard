import { X, Lock } from 'lucide-react';

/**
 * ActionDetailModal — Detailed security decision breakdown and explainable audit view.
 */
export default function ActionDetailModal({ action, onClose }) {
  if (!action) return null;

  const getRiskBadge = (level) => {
    const config = {
      LOW: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
      MEDIUM: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
      HIGH: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
      CRITICAL: 'bg-red-500/15 text-red-400 border-red-500/30',
    };
    return config[level] || config.MEDIUM;
  };

  const getDecisionBadge = (decision) => {
    const config = {
      ALLOW: 'status-badge-allow',
      APPROVED: 'status-badge-approved',
      REQUIRE_APPROVAL: 'status-badge-pending',
      BLOCK: 'status-badge-block',
      BLOCKED: 'status-badge-block',
      REJECTED: 'status-badge-rejected',
    };
    return config[decision] || 'status-badge-allow';
  };

  const getClassificationBadge = (cls) => {
    const config = {
      PRODUCTIVE: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      RELEVANT: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
      UNCERTAIN: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      UNRELATED: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
      DANGEROUS: 'bg-red-500/20 text-red-300 border-red-500/40',
    };
    return config[cls] || 'bg-gray-700 text-gray-300 border-gray-600';
  };

  const alignmentScore = action.goalAlignmentScore ?? action.alignmentScore ?? 100;
  const driftScore = action.driftScore ?? 0;
  const driftLevel = action.driftLevel ?? 'NORMAL';
  const hasViolations = action.violatedConstraints && action.violatedConstraints.length > 0;
  const classification = action.actionClassification || (hasViolations ? 'DANGEROUS' : alignmentScore >= 80 ? 'PRODUCTIVE' : 'UNCERTAIN');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-xl w-full max-w-xl mx-4 max-h-[90vh] overflow-y-auto animate-fade-in-up shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-bg-primary)]/50">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <Lock size={14} />
            </div>
            <div>
              <span className="text-xs font-bold tracking-wider uppercase text-[var(--color-text-primary)] block">
                Security Decision Breakdown
              </span>
              <span className="text-[0.65rem] text-[var(--color-text-muted)] font-mono">
                {action.actionId} | Goal Version {action.goalVersion || 1}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className={`text-[0.65rem] font-bold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${getClassificationBadge(classification)}`}>
              {classification}
            </span>
            <button
              onClick={onClose}
              className="text-[var(--color-text-muted)] hover:text-white transition-colors p-1"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {/* Action Overview */}
          <div className="p-3.5 rounded-lg bg-[var(--color-bg-primary)] border border-[var(--color-border)]">
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="text-xs font-mono font-bold text-cyan-400">
                {action.actionType} {action.target}
              </span>
              <span className={`status-badge ${getDecisionBadge(action.decision)}`}>
                {action.decision === 'BLOCK' ? 'BLOCKED' : action.decision}
              </span>
            </div>
            <p className="text-xs text-[var(--color-text-secondary)] italic mt-1">
              "{action.description || 'No description provided'}"
            </p>
          </div>

          {/* 6-Part Decision Breakdown Grid */}
          <div>
            <h4 className="text-[0.7rem] uppercase tracking-wider text-[var(--color-text-muted)] font-bold mb-2">
              Decision Analysis Pipeline
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
              {/* 1. Alignment */}
              <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-[var(--color-border)]">
                <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Goal Alignment
                </span>
                <span className={`text-base font-bold font-mono ${alignmentScore >= 80 ? 'text-emerald-400' : alignmentScore >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                  {alignmentScore}%
                </span>
                <span className="text-[0.65rem] text-[var(--color-text-muted)] block mt-0.5">
                  Status: {action.alignmentStatus || 'ALIGNED'}
                </span>
              </div>

              {/* 2. Constraint Check */}
              <div className={`p-3 rounded-lg border ${hasViolations ? 'bg-red-500/10 border-red-500/30' : 'bg-[var(--color-bg-primary)] border-emerald-500/20'}`}>
                <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Constraint Check
                </span>
                <span className={`text-base font-bold font-mono ${hasViolations ? 'text-red-400' : 'text-emerald-400'}`}>
                  {hasViolations ? 'VIOLATED' : 'PASSED'}
                </span>
                <span className="text-[0.65rem] text-[var(--color-text-muted)] block mt-0.5 truncate">
                  {hasViolations ? `${action.violatedConstraints.length} violations` : '0 violations'}
                </span>
              </div>

              {/* 3. Scope Check */}
              <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-[var(--color-border)]">
                <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Scope Boundary
                </span>
                <span className={`text-base font-bold font-mono ${action.scopeViolation ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {action.scopeViolation ? 'OUTSIDE SCOPE' : 'ALLOWED'}
                </span>
                <span className="text-[0.65rem] text-[var(--color-text-muted)] block mt-0.5">
                  Policy Boundary
                </span>
              </div>

              {/* 4. Risk Level */}
              <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-[var(--color-border)]">
                <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Contextual Risk
                </span>
                <span className={`text-sm font-bold block ${getRiskBadge(action.riskLevel)} w-fit px-2 py-0.5 rounded mt-0.5`}>
                  {action.riskLevel || 'LOW'} ({action.riskScore ?? 10}%)
                </span>
              </div>

              {/* 5. Goal Drift */}
              <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-[var(--color-border)]">
                <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Goal Drift
                </span>
                <span className={`text-base font-bold font-mono ${driftScore >= 50 ? 'text-red-400' : 'text-cyan-400'}`}>
                  {driftLevel} ({driftScore}%)
                </span>
                <span className="text-[0.65rem] text-[var(--color-text-muted)] block mt-0.5">
                  Multi-step trajectory
                </span>
              </div>

              {/* 6. Final Decision */}
              <div className="bg-[var(--color-bg-primary)] p-3 rounded-lg border border-cyan-500/20">
                <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Final Gateway Verdict
                </span>
                <span className="text-base font-bold font-mono text-cyan-400 block truncate">
                  {action.decision}
                </span>
                <span className="text-[0.65rem] text-[var(--color-text-muted)] block mt-0.5 font-mono">
                  {action.executionStatus}
                </span>
              </div>
            </div>
          </div>

          {/* Violated Constraints List if any */}
          {hasViolations && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
              <span className="text-[0.65rem] font-bold text-red-400 uppercase tracking-wider block mb-1">
                Violated Policy Constraints
              </span>
              <div className="flex flex-wrap gap-1.5">
                {action.violatedConstraints.map((vc, idx) => (
                  <span key={idx} className="text-[0.65rem] px-2 py-0.5 rounded bg-red-500/20 text-red-300 font-mono">
                    🚫 {vc}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Explainable Decision "WHY?" Statement */}
          <div>
            <span className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-bold block mb-1.5">
              Explainable Decision Statement (Why was this decision made?)
            </span>
            <div className="p-3.5 rounded-lg bg-[var(--color-bg-primary)] border border-cyan-500/30 text-xs text-slate-200 leading-relaxed font-sans">
              <span className="text-cyan-400 font-bold block mb-1">Gateway Explanation:</span>
              {action.reason}
            </div>
          </div>

          {/* Verification Result */}
          {action.verificationMessage && (
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs font-mono text-emerald-300">
              <span className="text-emerald-400 font-bold uppercase block text-[0.65rem] mb-0.5">
                Post-Execution Filesystem Proof:
              </span>
              {action.verificationMessage}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
