import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  ThumbsUp,
  AlertTriangle,
  Lock,
} from 'lucide-react';

/**
 * CompletionScreen — Final security summary after all actions are processed.
 */
export default function CompletionScreen({ goal, dashboard, onReset }) {
  if (!goal) return null;

  const total = dashboard?.totalActions || 0;
  const allowed = dashboard?.allowedActions || 0;
  const approved = dashboard?.approvedActions || 0;
  const blocked = (dashboard?.blockedActions || 0) + (dashboard?.rejectedActions || 0);
  const dangerousPrevented = dashboard?.dangerousActionsPrevented || 0;
  const integrityScore = Math.round(dashboard?.goalIntegrityScore || 0);

  const stats = [
    {
      label: 'Agent Actions',
      value: total,
      icon: CheckCircle2,
      color: 'text-blue-400',
    },
    {
      label: 'Allowed',
      value: allowed,
      icon: CheckCircle2,
      color: 'text-emerald-400',
    },
    {
      label: 'User Approved',
      value: approved,
      icon: ThumbsUp,
      color: 'text-cyan-400',
    },
    {
      label: 'Blocked',
      value: blocked,
      icon: XCircle,
      color: 'text-red-400',
    },
  ];

  const integrityColor =
    integrityScore >= 80 ? 'text-emerald-400' : integrityScore >= 50 ? 'text-amber-400' : 'text-red-400';

  return (
    <div className="glass-card p-8 text-center animate-fade-in-up max-w-xl mx-auto">
      {/* Shield Icon */}
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center mx-auto mb-5 shadow-lg shadow-emerald-500/20">
        <ShieldCheck size={32} className="text-white" />
      </div>

      {/* Title */}
      <h2 className="text-xl font-bold text-[var(--color-text-primary)] mb-1">
        TASK COMPLETED SAFELY
      </h2>
      <p className="text-sm text-[var(--color-text-muted)] mb-6">
        All agent actions have been processed through the security pipeline.
      </p>

      {/* Goal */}
      <div className="bg-[var(--color-bg-primary)] rounded-lg border border-[var(--color-border)] p-4 mb-6 text-left">
        <span className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold">
          Goal
        </span>
        <p className="text-sm text-[var(--color-text-primary)] mt-1">
          {goal.userGoal}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <div
              key={s.label}
              className="bg-[var(--color-bg-primary)] rounded-lg border border-[var(--color-border)] p-3"
            >
              <Icon size={16} className={`${s.color} mx-auto mb-1`} />
              <div className="text-xl font-bold text-[var(--color-text-primary)]">
                {s.value}
              </div>
              <div className="text-[0.6rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold">
                {s.label}
              </div>
            </div>
          );
        })}
      </div>

      {/* Dangerous Actions Prevented */}
      <div className="flex items-center justify-between bg-red-500/10 rounded-lg border border-red-500/20 p-3 mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle size={16} className="text-red-400" />
          <span className="text-xs font-semibold text-red-400">
            Dangerous Actions Prevented
          </span>
        </div>
        <span className="text-lg font-bold text-red-400">
          {dangerousPrevented}
        </span>
      </div>

      {/* Final Integrity */}
      <div className="flex items-center justify-between bg-[var(--color-bg-primary)] rounded-lg border border-[var(--color-border)] p-3 mb-4">
        <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
          Final Goal Integrity
        </span>
        <span className={`text-xl font-bold ${integrityColor}`}>
          {integrityScore}%
        </span>
      </div>

      {/* Security Status */}
      <div className="flex items-center justify-center gap-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20 p-3 mb-6">
        <Lock size={16} className="text-emerald-400" />
        <span className="text-sm font-bold text-emerald-400 uppercase tracking-wider">
          PROTECTED
        </span>
      </div>

      {/* Reset */}
      <button onClick={onReset} className="btn-primary w-full">
        RESET DEMO
      </button>
    </div>
  );
}
