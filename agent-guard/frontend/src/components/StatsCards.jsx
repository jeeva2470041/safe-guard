import {
  TrendingUp,
  ShieldAlert,
  Compass,
  CheckCircle2,
  XOctagon,
  Lock,
} from 'lucide-react';

/**
 * StatsCards — V5 Top Security & Telemetry metric cards.
 */
export default function StatsCards({ dashboard }) {
  if (!dashboard) return null;

  const integrity = dashboard.overallGoalIntegrity ?? dashboard.goalIntegrityScore ?? 100;
  const cumRisk = dashboard.cumulativeRiskScore ?? 0;
  const cumRiskLevel = dashboard.cumulativeRiskLevel ?? 'LOW';
  const driftScore = dashboard.currentDriftScore ?? 0;
  const driftLevel = dashboard.currentDriftLevel ?? 'NORMAL';
  const safetyScore = dashboard.agentSafetyScore ?? 100;

  return (
    <div className="space-y-3 animate-fade-in-up">
      <div className="grid grid-cols-2 gap-3">
        {/* Card 1: Goal Integrity */}
        <div className="glass-card p-4 flex flex-col items-center gap-1.5 border border-cyan-500/20">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <TrendingUp size={16} />
          </div>
          <span className={`text-2xl font-bold font-mono ${integrity >= 80 ? 'text-cyan-400' : integrity >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
            {integrity}%
          </span>
          <span className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold text-center">
            Goal Integrity
          </span>
        </div>

        {/* Card 2: Cumulative Risk */}
        <div className="glass-card p-4 flex flex-col items-center gap-1.5 border border-pink-500/20">
          <div className="w-8 h-8 rounded-lg bg-pink-500/10 border border-pink-500/30 flex items-center justify-center text-pink-400">
            <ShieldAlert size={16} />
          </div>
          <span className={`text-2xl font-bold font-mono ${cumRisk <= 30 ? 'text-emerald-400' : cumRisk <= 60 ? 'text-amber-400' : 'text-red-400'}`}>
            {cumRisk}%
          </span>
          <span className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold text-center">
            Risk: {cumRiskLevel}
          </span>
        </div>

        {/* Card 3: Multi-Step Drift */}
        <div className="glass-card p-4 flex flex-col items-center gap-1.5 border border-purple-500/20">
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Compass size={16} />
          </div>
          <span className={`text-2xl font-bold font-mono ${driftScore <= 20 ? 'text-emerald-400' : driftScore <= 50 ? 'text-amber-400' : 'text-red-400'}`}>
            {driftScore}%
          </span>
          <span className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold text-center">
            Drift: {driftLevel}
          </span>
        </div>

        {/* Card 4: Prototype Security Score */}
        <div className="glass-card p-4 flex flex-col items-center gap-1.5 border border-emerald-500/20">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Lock size={16} />
          </div>
          <span className={`text-2xl font-bold font-mono ${safetyScore >= 80 ? 'text-emerald-400' : safetyScore >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
            {safetyScore}
          </span>
          <span className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold text-center">
            Safety Score
          </span>
        </div>
      </div>

      {/* Allowed vs Blocked mini footer */}
      <div className="glass-card p-3 flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-1.5 text-emerald-400">
          <CheckCircle2 size={14} />
          <span>{(dashboard.allowedActions || 0) + (dashboard.approvedActions || 0)} Executed</span>
        </div>
        <div className="flex items-center gap-1.5 text-red-400">
          <XOctagon size={14} />
          <span>{(dashboard.blockedActions || 0) + (dashboard.rejectedActions || 0)} Blocked</span>
        </div>
      </div>
    </div>
  );
}
