import { X, Lock, ShieldCheck, Compass, ArrowRightLeft, Check, CheckCheck, Ban, OctagonAlert, AlertCircle } from 'lucide-react';

/**
 * ActionDetailModal — Detailed security decision breakdown and explainable audit view.
 * Supports Phase 1 & Phase 2:
 * - Intent Forensics, Source Trust, Sub-Goal hierarchy
 * - Consequence levels (LOW, MEDIUM, HIGH, CRITICAL)
 * - 4-choice Contextual Approval: Approve Once, Approve Similar Actions, Reject, Abort Session.
 */
export default function ActionDetailModal({ action, onClose, onApprove, onReject, onAbort }) {
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

  const getConsequenceBadge = (level) => {
    const config = {
      LOW: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
      MEDIUM: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
      HIGH: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
      CRITICAL: 'bg-red-500/15 text-red-400 border-red-500/30',
    };
    return config[level] || config.LOW;
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

  const getRelationshipBadge = (rel) => {
    const config = {
      DIRECTLY_RELEVANT: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
      SUPPORTING: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
      INDIRECTLY_RELEVANT: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
      UNRELATED: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
      CONTRADICTORY: 'bg-red-500/15 text-red-300 border-red-500/30',
    };
    return config[rel] || 'bg-slate-700 text-slate-300 border-slate-600';
  };

  const alignmentScore = action.goalAlignmentScore ?? action.alignmentScore ?? 100;
  const driftScore = action.driftScore ?? 0;
  const driftLevel = action.driftLevel ?? 'NORMAL';
  const hasViolations = action.violatedConstraints && action.violatedConstraints.length > 0;
  const classification = action.actionClassification || (hasViolations ? 'DANGEROUS' : alignmentScore >= 80 ? 'PRODUCTIVE' : 'UNCERTAIN');
  const goalRelationship = action.goalRelationship || action.goal_relationship || 'SUPPORTING';
  const source = action.source || 'USER';
  const subGoal = action.currentSubGoal || action.current_sub_goal;
  const reversibility = action.reversibility || 'REVERSIBLE';
  const consequenceLevel = action.consequenceLevel || (action.riskLevel === 'CRITICAL' ? 'CRITICAL' : action.riskLevel === 'HIGH' ? 'HIGH' : 'LOW');
  const isPendingApproval = action.executionStatus === 'PENDING_APPROVAL' || action.decision === 'REQUIRE_APPROVAL';

  return (
    <div className="modal-overlay p-3 sm:p-4" onClick={onClose}>
      <div
        className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-xl w-full max-w-xl max-h-[90vh] overflow-y-auto animate-fade-in-up shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 sm:px-6 py-3.5 sm:py-4 border-b border-[var(--color-border)] bg-[var(--color-bg-primary)]/50 gap-2">
          <div className="flex items-center gap-2 sm:gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shrink-0">
              <Lock size={14} />
            </div>
            <div className="min-w-0">
              <span className="text-xs font-bold tracking-wider uppercase text-[var(--color-text-primary)] block truncate">
                Security Decision Breakdown
              </span>
              <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] font-mono truncate block">
                {action.actionId} | v{action.goalVersion || 1}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            <span className={`text-[0.6rem] sm:text-[0.65rem] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${getClassificationBadge(classification)}`}>
              {classification}
            </span>
            <button
              onClick={onClose}
              className="text-[var(--color-text-muted)] hover:text-white transition-colors p-1"
            >
              <X size={17} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="px-4 sm:px-6 py-4 sm:py-5 space-y-4">
          {/* Action Overview */}
          <div className="p-3 sm:p-3.5 rounded-lg bg-[var(--color-bg-primary)] border border-[var(--color-border)] min-w-0">
            <div className="flex flex-wrap items-center justify-between gap-1.5 mb-1">
              <span className="text-xs font-mono font-bold text-cyan-400 break-all">
                {action.actionType} {action.target}
              </span>
              <span className={`status-badge text-[0.65rem] px-2 py-0.5 shrink-0 ${getDecisionBadge(action.decision)}`}>
                {action.decision === 'BLOCK' ? 'BLOCKED' : action.decision}
              </span>
            </div>
            {action.description && (
              <p className="text-[0.7rem] sm:text-xs text-[var(--color-text-secondary)] italic mt-1 break-words leading-relaxed">
                "{action.description}"
              </p>
            )}

            {/* Metadata Badges */}
            <div className="flex flex-wrap items-center gap-1.5 mt-2.5 pt-2 border-t border-[var(--color-border)]/60 text-[0.65rem]">
              <span className={`px-2 py-0.5 rounded border font-mono ${getRelationshipBadge(goalRelationship)}`}>
                {goalRelationship}
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300 font-mono">
                Source: {source}
              </span>
              <span className={`px-2 py-0.5 rounded border font-mono ${getConsequenceBadge(consequenceLevel)}`}>
                Consequence: {consequenceLevel}
              </span>
              <span className={`px-2 py-0.5 rounded border font-mono ${reversibility === 'IRREVERSIBLE' ? 'bg-red-500/15 border-red-500/30 text-red-300' : 'bg-emerald-500/10 border-emerald-500/25 text-emerald-300'}`}>
                {reversibility}
              </span>
              {subGoal && (
                <span className="px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/30 text-blue-300 font-mono">
                  Sub-Goal: {subGoal}
                </span>
              )}
            </div>
          </div>

          {/* Contextual Approval Card (Phase 2) */}
          {isPendingApproval && (
            <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/30 space-y-3">
              <div className="flex items-center gap-2 text-amber-400 font-bold text-xs uppercase tracking-wider">
                <AlertCircle size={15} />
                <span>Action Requires Contextual Human Authorization</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                This action involves elevated financial or external impact. Select your authorization policy:
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                <button
                  onClick={() => onApprove && onApprove(action.actionId, 'ONCE')}
                  className="flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-colors shadow"
                >
                  <Check size={13} />
                  <span>Approve Once</span>
                </button>
                <button
                  onClick={() => onApprove && onApprove(action.actionId, 'SIMILAR')}
                  className="flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs transition-colors shadow"
                >
                  <CheckCheck size={13} />
                  <span>Approve Similar</span>
                </button>
                <button
                  onClick={() => onReject && onReject(action.actionId)}
                  className="flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs transition-colors shadow"
                >
                  <Ban size={13} />
                  <span>Reject</span>
                </button>
                <button
                  onClick={() => onAbort && onAbort(action.goalId)}
                  className="flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold text-xs transition-colors shadow"
                >
                  <OctagonAlert size={13} />
                  <span>Abort Session</span>
                </button>
              </div>
            </div>
          )}

          {/* 6-Part Decision Breakdown Grid */}
          <div>
            <h4 className="text-[0.65rem] sm:text-[0.7rem] uppercase tracking-wider text-[var(--color-text-muted)] font-bold mb-2">
              Decision Analysis Pipeline
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-2.5 text-xs">
              {/* 1. Alignment */}
              <div className="bg-[var(--color-bg-primary)] p-2.5 sm:p-3 rounded-lg border border-[var(--color-border)]">
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Goal Alignment
                </span>
                <span className={`text-sm sm:text-base font-bold font-mono ${alignmentScore >= 75 ? 'text-emerald-400' : alignmentScore >= 45 ? 'text-amber-400' : 'text-red-400'}`}>
                  {alignmentScore}%
                </span>
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] block mt-0.5 truncate">
                  {action.alignmentStatus || 'ALIGNED'}
                </span>
              </div>

              {/* 2. Constraint Check */}
              <div className={`p-2.5 sm:p-3 rounded-lg border ${hasViolations ? 'bg-red-500/10 border-red-500/30' : 'bg-[var(--color-bg-primary)] border-emerald-500/20'}`}>
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Constraint Check
                </span>
                <span className={`text-sm sm:text-base font-bold font-mono ${hasViolations ? 'text-red-400' : 'text-emerald-400'}`}>
                  {hasViolations ? 'VIOLATED' : 'PASSED'}
                </span>
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] block mt-0.5 truncate">
                  {hasViolations ? `${action.violatedConstraints.length} violations` : '0 violations'}
                </span>
              </div>

              {/* 3. Scope Check */}
              <div className="bg-[var(--color-bg-primary)] p-2.5 sm:p-3 rounded-lg border border-[var(--color-border)]">
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Scope Boundary
                </span>
                <span className={`text-sm sm:text-base font-bold font-mono ${action.scopeViolation ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {action.scopeViolation ? 'OUTSIDE' : 'ALLOWED'}
                </span>
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] block mt-0.5 truncate">
                  Policy Boundary
                </span>
              </div>

              {/* 4. Risk Level */}
              <div className="bg-[var(--color-bg-primary)] p-2.5 sm:p-3 rounded-lg border border-[var(--color-border)]">
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Contextual Risk
                </span>
                <span className={`text-xs sm:text-sm font-bold block ${getRiskBadge(action.riskLevel)} w-fit px-1.5 py-0.5 rounded mt-0.5`}>
                  {action.riskLevel || 'LOW'} ({action.riskScore ?? 10}%)
                </span>
              </div>

              {/* 5. Goal Drift */}
              <div className="bg-[var(--color-bg-primary)] p-2.5 sm:p-3 rounded-lg border border-[var(--color-border)]">
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Goal Drift
                </span>
                <span className={`text-sm sm:text-base font-bold font-mono ${driftScore >= 50 ? 'text-red-400' : 'text-cyan-400'}`}>
                  {driftLevel} ({driftScore}%)
                </span>
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] block mt-0.5 truncate">
                  Multi-step
                </span>
              </div>

              {/* 6. Final Decision */}
              <div className="bg-[var(--color-bg-primary)] p-2.5 sm:p-3 rounded-lg border border-cyan-500/20">
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] uppercase block font-semibold">
                  Gateway Verdict
                </span>
                <span className="text-sm sm:text-base font-bold font-mono text-cyan-400 block truncate">
                  {action.decision}
                </span>
                <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] block mt-0.5 font-mono truncate">
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
                  <span key={idx} className="text-[0.65rem] px-2 py-0.5 rounded bg-red-500/20 text-red-300 font-mono break-all">
                    🚫 {vc}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Phase 3 Attack Containment Alert */}
          {(action.isGoalHijacked || action.reason?.includes('Attack Containment') || action.reason?.includes('Prompt Injection') || action.reason?.includes('Exfiltration')) && (
            <div className="p-3 rounded-lg bg-red-500/15 border border-red-500/40 space-y-1">
              <div className="flex items-center gap-1.5 text-red-400 font-bold text-xs uppercase tracking-wider">
                <OctagonAlert size={14} />
                <span>Phase 3 Runtime Attack Containment Active</span>
              </div>
              <p className="text-[0.7rem] text-red-200">
                Security engine detected high-confidence attack vector (Prompt Injection, Trajectory Hijacking, Credential Extraction, or Data Exfiltration).
              </p>
            </div>
          )}

          {/* Explainable Decision "WHY?" Statement */}
          <div>
            <span className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-bold block mb-1.5">
              Explainable Decision Statement (Why was this decision made?)
            </span>
            <div className="p-3 sm:p-3.5 rounded-lg bg-[var(--color-bg-primary)] border border-cyan-500/30 text-xs text-slate-200 leading-relaxed font-sans break-words">
              <span className="text-cyan-400 font-bold block mb-1">Gateway Explanation:</span>
              {action.reason}
            </div>
          </div>

          {/* Verification Result */}
          {action.verificationMessage && (
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs font-mono text-emerald-300 break-words">
              <span className="text-emerald-400 font-bold uppercase block text-[0.65rem] mb-0.5">
                Post-Execution Verification Proof:
              </span>
              {action.verificationMessage}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
