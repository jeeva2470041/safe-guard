import { ShieldCheck } from 'lucide-react';

/**
 * GoalIntegrityCard — Displays the average goal integrity score
 * with a circular progress ring and alignment breakdown.
 */
export default function GoalIntegrityCard({ actions = [], score = 0 }) {
  const safeActions = Array.isArray(actions) ? actions : [];
  const aligned = safeActions.filter(a => a && a.alignmentStatus === 'ALIGNED').length;
  const partial = safeActions.filter(a => a && a.alignmentStatus === 'PARTIALLY_ALIGNED').length;
  const unaligned = safeActions.filter(a => a && a.alignmentStatus === 'UNALIGNED').length;

  // SVG ring calculation
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(100, Math.max(0, score));
  const offset = circumference - (pct / 100) * circumference;

  // Color based on score
  let strokeColor = '#ef4444'; // red
  if (pct >= 80) strokeColor = '#10b981'; // emerald
  else if (pct >= 50) strokeColor = '#f59e0b'; // amber

  return (
    <div className="glass-card p-5 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center gap-2 mb-5">
        <ShieldCheck size={16} className="text-emerald-400" />
        <span className="text-xs font-semibold tracking-wider uppercase text-[var(--color-text-muted)]">
          Goal Integrity
        </span>
      </div>

      {/* Score Ring */}
      <div className="flex items-center justify-center mb-5">
        <div className="relative w-32 h-32">
          <svg
            viewBox="0 0 100 100"
            className="score-ring w-full h-full"
          >
            <circle
              cx="50"
              cy="50"
              r={radius}
              className="score-ring-track"
            />
            <circle
              cx="50"
              cy="50"
              r={radius}
              className="score-ring-fill"
              stroke={strokeColor}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className="text-3xl font-bold"
              style={{ color: strokeColor }}
            >
              {Math.round(pct)}
            </span>
            <span className="text-[0.6rem] text-[var(--color-text-muted)] uppercase tracking-widest">
              Score
            </span>
          </div>
        </div>
      </div>

      {/* Alignment breakdown */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-[var(--color-text-secondary)]">Aligned</span>
          </div>
          <span className="font-semibold text-emerald-400">{aligned}</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span className="text-[var(--color-text-secondary)]">Partially Aligned</span>
          </div>
          <span className="font-semibold text-amber-400">{partial}</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-[var(--color-text-secondary)]">Unaligned</span>
          </div>
          <span className="font-semibold text-red-400">{unaligned}</span>
        </div>
      </div>

      {/* Goal Drift Meter */}
      {safeActions.length > 0 && (
        <div className="border-t border-[var(--color-border)] pt-3 mt-3">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-[0.65rem] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
              Dynamic Goal Drift
            </span>
            <span className={`text-xs font-mono font-bold ${
              (safeActions[safeActions.length - 1]?.driftScore || 0) >= 50 ? 'text-red-400' : 'text-emerald-400'
            }`}>
              {safeActions[safeActions.length - 1]?.driftScore || 0}%
            </span>
          </div>
          <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                (safeActions[safeActions.length - 1]?.driftScore || 0) >= 50 ? 'bg-red-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(100, safeActions[safeActions.length - 1]?.driftScore || 0)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
