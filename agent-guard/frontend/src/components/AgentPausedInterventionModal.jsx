import React, { useState, useEffect } from 'react';
import { AlertOctagon, Play, Square, Edit3, ShieldAlert, Sparkles, X } from 'lucide-react';

/**
 * AgentPausedInterventionModal — High-visibility security intervention modal and banner
 * triggered when the Security Gateway automatically pauses the agent due to critical drift or risk.
 */
export default function AgentPausedInterventionModal({
  originalGoal = '',
  originalConstraints = [],
  goalVersion = 1,
  pauseReason = '',
  recentDivergentAction = '',
  overallGoalIntegrity = 0,
  cumulativeRiskLevel = 'CRITICAL',
  cumulativeRiskScore = 85,
  onResume,
  onStop,
  onModifyGoal,
}) {
  const [showModifyModal, setShowModifyModal] = useState(false);
  const [updatedGoal, setUpdatedGoal] = useState(originalGoal || '');
  const [updatedConstraints, setUpdatedConstraints] = useState(
    Array.isArray(originalConstraints) && originalConstraints.length > 0
      ? originalConstraints.join(', ')
      : ''
  );
  const [changeReason, setChangeReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Sync inputs dynamically whenever originalGoal or constraints update from backend polling
  useEffect(() => {
    if (originalGoal) {
      setUpdatedGoal(originalGoal);
    }
    if (Array.isArray(originalConstraints) && originalConstraints.length > 0) {
      setUpdatedConstraints(originalConstraints.join(', '));
    } else {
      setUpdatedConstraints('');
    }
  }, [originalGoal, originalConstraints]);

  const handleModifySubmit = async (e) => {
    e.preventDefault();
    if (!updatedGoal.trim()) return;
    setIsSubmitting(true);
    try {
      const constraintsArray = updatedConstraints
        .split(',')
        .map((c) => c.trim())
        .filter(Boolean);
      await onModifyGoal(updatedGoal, constraintsArray, changeReason);
      setShowModifyModal(false);
    } catch (err) {
      console.error('Failed to modify goal:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {/* High-Contrast Intervention Banner */}
      <div className="glass-card p-6 border-2 border-red-500/60 bg-gradient-to-r from-red-950/70 via-slate-900/90 to-red-950/70 mb-6 shadow-2xl animate-pulse-border">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Left info */}
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/50 flex items-center justify-center text-red-400 shrink-0">
                <AlertOctagon size={24} className="animate-bounce" />
              </div>
              <div>
                <span className="text-[0.65rem] font-bold px-2.5 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/40 uppercase tracking-widest">
                  CRITICAL DRIFT & RISK INTERVENTION
                </span>
                <h3 className="text-lg font-extrabold text-red-400 tracking-tight mt-0.5">
                  AGENT AUTOMATICALLY PAUSED
                </h3>
              </div>
            </div>

            <p className="text-xs text-[var(--color-text-secondary)] font-mono bg-black/40 p-2.5 rounded-lg border border-red-500/30">
              <span className="text-red-400 font-bold">Intervention Reason: </span>
              {pauseReason || 'Agent behavior has significantly diverged from the original goal policy.'}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs pt-1">
              <div className="bg-black/30 p-2 rounded border border-[var(--color-border)]">
                <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block">Original User Goal</span>
                <span className="text-slate-200 font-medium truncate block">{originalGoal || 'Not specified'}</span>
              </div>
              <div className="bg-black/30 p-2 rounded border border-[var(--color-border)]">
                <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block">Recent Divergent Action</span>
                <span className="text-red-300 font-mono font-bold truncate block">{recentDivergentAction || 'Out-of-scope operation'}</span>
              </div>
              <div className="bg-black/30 p-2 rounded border border-[var(--color-border)]">
                <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase block">Integrity vs Risk</span>
                <span className="text-amber-300 font-mono font-bold">
                  {overallGoalIntegrity}% Integrity | {cumulativeRiskLevel} ({cumulativeRiskScore}%)
                </span>
              </div>
            </div>
          </div>

          {/* Right Action Controls */}
          <div className="flex flex-wrap lg:flex-col gap-2.5 shrink-0 justify-end">
            <button
              onClick={() => setShowModifyModal(true)}
              className="px-4 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/30 transition-all cursor-pointer"
            >
              <Edit3 size={15} />
              MODIFY GOAL (V{(goalVersion || 1) + 1})
            </button>
            <button
              onClick={onResume}
              className="px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/30 transition-all cursor-pointer"
            >
              <Play size={15} />
              RESUME AGENT
            </button>
            <button
              onClick={onStop}
              className="px-4 py-2.5 rounded-lg bg-red-700 hover:bg-red-600 text-white font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg shadow-red-700/30 transition-all cursor-pointer"
            >
              <Square size={15} />
              STOP AGENT
            </button>
          </div>
        </div>
      </div>

      {/* Modify Goal Modal */}
      {showModifyModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-xl w-full p-6 border border-cyan-500/40 bg-[var(--color-bg-secondary)] shadow-2xl animate-fade-in-up">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border)] mb-4">
              <div className="flex items-center gap-2">
                <Sparkles size={18} className="text-cyan-400" />
                <h3 className="text-base font-bold text-[var(--color-text-primary)]">
                  Modify Active Goal & Create Version {(goalVersion || 1) + 1}
                </h3>
              </div>
              <button
                onClick={() => setShowModifyModal(false)}
                className="text-gray-400 hover:text-white p-1"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleModifySubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-[var(--color-text-muted)] uppercase font-semibold mb-1">
                  Updated Goal Statement
                </label>
                <textarea
                  value={updatedGoal}
                  onChange={(e) => setUpdatedGoal(e.target.value)}
                  rows={3}
                  className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg p-2.5 text-slate-200 focus:border-cyan-500 focus:outline-none"
                  placeholder="Enter updated natural language goal..."
                  required
                />
              </div>

              <div>
                <label className="block text-[var(--color-text-muted)] uppercase font-semibold mb-1">
                  Updated Constraints (comma-separated)
                </label>
                <input
                  type="text"
                  value={updatedConstraints}
                  onChange={(e) => setUpdatedConstraints(e.target.value)}
                  className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg p-2.5 text-slate-200 focus:border-cyan-500 focus:outline-none"
                  placeholder="e.g., Do not access secrets, Do not delete database"
                />
              </div>

              <div>
                <label className="block text-[var(--color-text-muted)] uppercase font-semibold mb-1">
                  Reason for Scope Change
                </label>
                <input
                  type="text"
                  value={changeReason}
                  onChange={(e) => setChangeReason(e.target.value)}
                  className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg p-2.5 text-slate-200 focus:border-cyan-500 focus:outline-none"
                  placeholder="e.g. Updating task parameters to expand scope"
                />
              </div>

              <div className="bg-cyan-500/10 border border-cyan-500/30 p-3 rounded-lg flex items-start gap-2.5 text-[0.7rem] text-cyan-300">
                <ShieldAlert size={16} className="shrink-0 mt-0.5 text-cyan-400" />
                <span>
                  Modifying the goal will generate a new versioned Goal Policy. Past actions will retain their Version {goalVersion || 1} audit records.
                </span>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModifyModal(false)}
                  className="px-4 py-2 rounded-lg border border-[var(--color-border)] text-gray-300 hover:bg-white/5"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold tracking-wider uppercase cursor-pointer"
                >
                  {isSubmitting ? 'UPDATING...' : 'APPLY NEW GOAL VERSION'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
