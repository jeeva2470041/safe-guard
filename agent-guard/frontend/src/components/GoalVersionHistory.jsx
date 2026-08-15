import React from 'react';
import { History } from 'lucide-react';

/**
 * GoalVersionHistory — Displays the complete version history timeline for the active goal.
 */
export default function GoalVersionHistory({ goalVersion = 1, versionHistory = [] }) {
  const historyList = versionHistory.length > 0
    ? versionHistory
    : [
        {
          version: 1,
          userGoal: 'Initial established user goal',
          createdAt: new Date().toISOString(),
          changeReason: 'Original Goal Setup',
          status: 'ACTIVE'
        }
      ];

  return (
    <div className="glass-card p-6 mb-6 border border-[var(--color-border)]">
      <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border)] mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <History size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-wide uppercase text-[var(--color-text-primary)]">
              Goal Policy Version History
            </h3>
            <p className="text-[0.7rem] text-[var(--color-text-muted)]">
              Full versioning trail preserving goal snapshots and scope evolution
            </p>
          </div>
        </div>

        <span className="text-[0.65rem] font-bold px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30 font-mono uppercase">
          Current: Version {goalVersion}
        </span>
      </div>

      <div className="space-y-3">
        {historyList.map((ver, idx) => {
          const isActive = ver.version === goalVersion;
          return (
            <div
              key={idx}
              className={`p-3.5 rounded-lg border transition-all ${
                isActive
                  ? 'border-cyan-500/50 bg-cyan-950/20 shadow-md shadow-cyan-500/10'
                  : 'border-[var(--color-border)] bg-[var(--color-bg-primary)] opacity-70'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold px-2 py-0.5 rounded font-mono ${isActive ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40' : 'bg-gray-800 text-gray-300'}`}>
                    VERSION {ver.version}
                  </span>
                  <span className="text-xs font-semibold text-[var(--color-text-primary)]">
                    {ver.changeReason || 'User update'}
                  </span>
                </div>
                <span className="text-[0.65rem] text-[var(--color-text-muted)] font-mono">
                  {ver.createdAt ? new Date(ver.createdAt).toLocaleTimeString() : 'Recent'}
                </span>
              </div>

              <p className="text-xs text-[var(--color-text-secondary)] italic mb-2">
                "{ver.userGoal}"
              </p>

              {ver.constraints && ver.constraints.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {ver.constraints.map((c, cIdx) => (
                    <span
                      key={cIdx}
                      className="text-[0.65rem] px-2 py-0.5 rounded bg-black/40 border border-red-500/20 text-red-300 font-mono"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
