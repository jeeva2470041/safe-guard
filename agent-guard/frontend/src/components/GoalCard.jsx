import { Target, Tag, Hash } from 'lucide-react';

/**
 * GoalCard — Displays the current user goal, ID, status, and constraints.
 */
export default function GoalCard({ goal }) {
  if (!goal) return null;

  const statusColors = {
    ACTIVE: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
    RUNNING: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
    WAITING_FOR_APPROVAL: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    BLOCKED_ACTION: 'text-red-400 bg-red-500/10 border-red-500/30',
    COMPLETED: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
    FAILED: 'text-red-500 bg-red-600/10 border-red-600/30',
    STOPPED: 'text-gray-400 bg-gray-500/10 border-gray-500/30',
  };

  return (
    <div className="glass-card p-5 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-4">
        <div className="flex items-center gap-2">
          <Target size={16} className="text-blue-400" />
          <span className="text-xs font-semibold tracking-wider uppercase text-[var(--color-text-muted)]">
            Current User Goal
          </span>
        </div>
        <span className="text-[0.65rem] font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-wide">
          {goal.agent ? (goal.agent.toLowerCase() === 'antigravity' ? 'GOOGLE ANTIGRAVITY' : `${goal.agent.toUpperCase()} AGENT`) : 'OPENAI AGENT'}
        </span>
      </div>

      {/* Goal text */}
      <p className="text-base font-medium text-[var(--color-text-primary)] mb-4 leading-relaxed">
        "{goal.userGoal}"
      </p>

      {/* Meta row */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex items-center gap-1.5">
          <Hash size={13} className="text-[var(--color-text-muted)]" />
          <span className="text-xs font-mono text-[var(--color-text-secondary)]">
            {goal.goalId}
          </span>
        </div>

        <span
          className={`text-[0.7rem] font-semibold px-2.5 py-0.5 rounded-full border ${
            statusColors[goal.status] || statusColors.ACTIVE
          }`}
        >
          {goal.status}
        </span>
      </div>

      {/* Dynamic Policy Scopes */}
      {goal.goalPolicy && (
        <div className="border-t border-[var(--color-border)] pt-3 mt-3 space-y-2">
          <div className="text-[0.65rem] uppercase tracking-wider text-cyan-400 font-bold flex items-center justify-between">
            <span>System Policy Scope</span>
            <span className="font-mono text-[var(--color-text-muted)]">{goal.goalPolicy.domain || 'general'}</span>
          </div>

          {/* Allowed Scope */}
          {goal.goalPolicy.allowedScope && goal.goalPolicy.allowedScope.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {goal.goalPolicy.allowedScope.map((scope, idx) => (
                <span key={idx} className="text-[0.65rem] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  ✓ {scope}
                </span>
              ))}
            </div>
          )}

          {/* Restricted Scope */}
          {goal.goalPolicy.restrictedScope && goal.goalPolicy.restrictedScope.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {goal.goalPolicy.restrictedScope.map((scope, idx) => (
                <span key={idx} className="text-[0.65rem] px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                  🚫 {scope}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Constraints */}
      {goal.constraints && goal.constraints.length > 0 && (
        <div className="border-t border-[var(--color-border)] pt-3 mt-2">
          <span className="text-[0.7rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold flex items-center gap-1.5 mb-2">
            <Tag size={12} />
            Constraints
          </span>
          <div className="flex flex-wrap gap-2">
            {goal.constraints.map((c, i) => (
              <span
                key={i}
                className="text-[0.7rem] px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20"
              >
                {c}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
