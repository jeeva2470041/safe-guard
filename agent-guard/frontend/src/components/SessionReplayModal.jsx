import { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  Shield,
  ShieldAlert,
  Flame,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileCode,
  Radio,
  Sparkles,
  ArrowRight,
  Database,
  Globe,
  KeyRound,
  Lock,
  Layers,
  Zap,
  Activity,
  ExternalLink,
  X,
} from 'lucide-react';
import { getSessionReplay } from '../services/api';

/**
 * SessionReplayModal — Interactive Step-by-Step Trajectory Replay Viewer.
 * Visual sequence: USER GOAL -> ACTION 1 -> ACTION 2 -> ACTION 3 -> ATTACK -> BLOCK
 */
export default function SessionReplayModal({ isOpen, onClose, goalId }) {
  const [replayData, setReplayData] = useState(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(1500); // ms per step
  const [loading, setLoading] = useState(true);

  const timerRef = useRef(null);

  useEffect(() => {
    if (isOpen && goalId) {
      setLoading(true);
      getSessionReplay(goalId)
        .then((data) => {
          setReplayData(data);
          setCurrentStepIndex(0);
        })
        .catch((err) => console.error('Failed to load session replay:', err))
        .finally(() => setLoading(false));
    } else {
      setIsPlaying(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  }, [isOpen, goalId]);

  // Auto-play progression loop
  useEffect(() => {
    if (isPlaying && replayData?.steps?.length > 0) {
      timerRef.current = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= replayData.steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, playSpeed);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playSpeed, replayData]);

  if (!isOpen) return null;

  const steps = replayData?.steps || [];
  const activeStep = steps[currentStepIndex] || {};
  const isAttack = Boolean(activeStep.isAttackEvent);
  const isTerminal = currentStepIndex === steps.length - 1;

  const getDecisionBadge = (decision) => {
    switch (decision) {
      case 'ALLOW':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
      case 'REQUIRE_APPROVAL':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40 animate-pulse';
      case 'BLOCK':
        return 'bg-red-500/20 text-red-400 border-red-500/40 animate-pulse font-extrabold';
      default:
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-xl animate-fade-in">
      <div className="card w-full max-w-5xl max-h-[92vh] flex flex-col rounded-3xl border border-cyan-500/40 shadow-2xl shadow-cyan-500/20 overflow-hidden bg-[var(--color-bg-secondary)]">
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-[var(--color-border)] flex items-center justify-between bg-gradient-to-r from-blue-950/40 via-[var(--color-bg-primary)] to-[var(--color-bg-secondary)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20">
              <Sparkles size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-extrabold text-white tracking-tight">
                  Autonomous Session Trajectory Replay
                </h2>
                <span className="text-[0.65rem] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-bold">
                  {goalId}
                </span>
              </div>
              <p className="text-xs text-[var(--color-text-muted)] truncate max-w-xl">
                Goal: <span className="text-white font-medium">{replayData?.userGoal || 'Executing agent plan'}</span>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Replay Controls & Timeline Scrubber */}
        <div className="px-5 py-3.5 border-b border-[var(--color-border)] bg-[var(--color-bg-primary)] flex flex-col sm:flex-row items-center justify-between gap-3">
          {/* Playback Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentStepIndex(0)}
              className="p-2 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)] hover:border-cyan-500/50 text-gray-300 hover:text-white transition-all"
              title="First Step"
            >
              <SkipBack size={14} />
            </button>
            <button
              onClick={() => setCurrentStepIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentStepIndex === 0}
              className="px-3 py-1.5 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)] hover:border-cyan-500/50 text-xs font-bold text-gray-300 hover:text-white disabled:opacity-40 transition-all"
            >
              Prev
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-4 py-1.5 rounded-lg btn-primary text-xs font-extrabold flex items-center gap-1.5 shadow-md shadow-cyan-500/20"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
            >
              {isPlaying ? <Pause size={13} /> : <Play size={13} />}
              <span>{isPlaying ? 'Pause' : 'Play Replay'}</span>
            </button>
            <button
              onClick={() => setCurrentStepIndex((prev) => Math.min(steps.length - 1, prev + 1))}
              disabled={currentStepIndex >= steps.length - 1}
              className="px-3 py-1.5 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)] hover:border-cyan-500/50 text-xs font-bold text-gray-300 hover:text-white disabled:opacity-40 transition-all"
            >
              Next
            </button>
            <button
              onClick={() => setCurrentStepIndex(steps.length - 1)}
              className="p-2 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)] hover:border-cyan-500/50 text-gray-300 hover:text-white transition-all"
              title="Last Step"
            >
              <SkipForward size={14} />
            </button>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-[var(--color-text-muted)] font-medium">Speed:</span>
            {[
              { label: '1x', speed: 1800 },
              { label: '2x', speed: 900 },
              { label: '4x', speed: 450 },
            ].map((spd) => (
              <button
                key={spd.label}
                onClick={() => setPlaySpeed(spd.speed)}
                className={`px-2 py-0.5 rounded text-[0.65rem] font-bold font-mono transition-all ${
                  playSpeed === spd.speed
                    ? 'bg-cyan-500 text-black shadow-sm'
                    : 'bg-[var(--color-bg-secondary)] text-gray-300 border border-[var(--color-border)]'
                }`}
              >
                {spd.label}
              </button>
            ))}

            <span className="font-mono text-xs font-bold text-cyan-400 ml-2">
              Step {currentStepIndex + 1} of {steps.length}
            </span>
          </div>
        </div>

        {/* Step Flow Breadcrumb Pills */}
        <div className="p-3 bg-[var(--color-bg-primary)]/70 border-b border-[var(--color-border)] overflow-x-auto no-scrollbar">
          <div className="flex items-center gap-1.5 min-w-max">
            {steps.map((step, idx) => {
              const isCurrent = currentStepIndex === idx;
              const isPast = currentStepIndex > idx;
              const isStepAttack = step.isAttackEvent || step.decision === 'BLOCK';

              return (
                <div key={idx} className="flex items-center gap-1.5">
                  <button
                    onClick={() => setCurrentStepIndex(idx)}
                    className={`px-2.5 py-1 rounded-lg text-[0.65rem] font-bold font-mono transition-all flex items-center gap-1.5 ${
                      isCurrent
                        ? isStepAttack
                          ? 'bg-red-500 text-white shadow-lg shadow-red-500/40 ring-2 ring-red-400'
                          : 'bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-md shadow-blue-500/30'
                        : isPast
                        ? isStepAttack
                          ? 'bg-red-950/40 text-red-400 border border-red-500/50'
                          : 'bg-emerald-950/30 text-emerald-400 border border-emerald-500/30'
                        : 'bg-[var(--color-bg-secondary)] text-gray-400 border border-[var(--color-border)] hover:border-gray-600'
                    }`}
                  >
                    <span>{step.stepType === 'GOAL_INITIALIZATION' ? 'GOAL' : `ACT ${idx}`}</span>
                    {isStepAttack && <Flame size={10} className="text-red-300 animate-pulse" />}
                  </button>

                  {idx < steps.length - 1 && (
                    <ArrowRight size={11} className="text-[var(--color-text-muted)]" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Deep-Dive Inspector */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 no-scrollbar">
          {loading ? (
            <div className="py-20 text-center text-gray-400 text-xs animate-pulse">
              Loading session trajectory replay...
            </div>
          ) : (
            <div className="space-y-4">
              {/* Step Title Banner */}
              <div
                className={`p-4 rounded-2xl border transition-all ${
                  isAttack
                    ? 'bg-gradient-to-br from-red-950/50 via-rose-950/30 to-[var(--color-bg-primary)] border-red-500/60 shadow-xl shadow-red-500/20 ring-1 ring-red-500/40'
                    : 'bg-gradient-to-br from-blue-950/30 via-cyan-950/20 to-[var(--color-bg-primary)] border-cyan-500/40 shadow-lg'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    {isAttack ? (
                      <div className="w-8 h-8 rounded-xl bg-red-500 flex items-center justify-center text-white shadow-md shadow-red-500/50 animate-pulse">
                        <Flame size={18} />
                      </div>
                    ) : (
                      <div className="w-8 h-8 rounded-xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
                        <Activity size={16} />
                      </div>
                    )}
                    <div>
                      <div className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">
                        {activeStep.stepType} &bull; Step {currentStepIndex + 1}/{steps.length}
                      </div>
                      <h3 className="text-sm font-extrabold text-white mt-0.5">
                        {activeStep.title}
                      </h3>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-bold px-2.5 py-1 rounded-lg border ${getDecisionBadge(
                        activeStep.decision
                      )}`}
                    >
                      {activeStep.decision || 'INITIALIZED'}
                    </span>
                  </div>
                </div>

                {isAttack && (
                  <div className="mt-3 pt-3 border-t border-red-500/30 flex items-center gap-2 text-xs text-red-300 font-bold">
                    <ShieldAlert size={16} className="text-red-400 shrink-0 animate-pulse" />
                    <span>
                      AGENT GUARD CONTAINMENT INTERCEPTION: Malicious action was safely blocked before execution.
                    </span>
                  </div>
                )}
              </div>

              {/* 3-Column Telemetry Gauges */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)]">
                  <div className="text-[0.65rem] font-bold text-[var(--color-text-muted)] uppercase">
                    Goal Alignment Score
                  </div>
                  <div className="text-xl font-extrabold text-white mt-1 flex items-center justify-between">
                    <span>{activeStep.goalAlignmentScore ?? 100}%</span>
                    <span className="text-[0.65rem] font-mono text-cyan-400 font-normal">
                      {activeStep.goalRelationship || 'SUPPORTING'}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700/50 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        (activeStep.goalAlignmentScore ?? 100) >= 70 ? 'bg-emerald-400' : 'bg-red-400'
                      }`}
                      style={{ width: `${activeStep.goalAlignmentScore ?? 100}%` }}
                    />
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)]">
                  <div className="text-[0.65rem] font-bold text-[var(--color-text-muted)] uppercase">
                    Multi-Step Drift Score
                  </div>
                  <div className="text-xl font-extrabold text-white mt-1 flex items-center justify-between">
                    <span>{activeStep.driftScore ?? 0}%</span>
                    <span
                      className={`text-[0.65rem] font-mono font-bold ${
                        (activeStep.driftScore ?? 0) >= 60 ? 'text-red-400' : 'text-emerald-400'
                      }`}
                    >
                      {activeStep.driftScore >= 80 ? 'CRITICAL' : activeStep.driftScore >= 40 ? 'HIGH' : 'NORMAL'}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700/50 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        (activeStep.driftScore ?? 0) >= 60 ? 'bg-red-500' : 'bg-cyan-400'
                      }`}
                      style={{ width: `${activeStep.driftScore ?? 0}%` }}
                    />
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)]">
                  <div className="text-[0.65rem] font-bold text-[var(--color-text-muted)] uppercase">
                    Calculated Risk Level
                  </div>
                  <div className="text-xl font-extrabold text-white mt-1 flex items-center justify-between">
                    <span
                      className={
                        activeStep.riskLevel === 'CRITICAL'
                          ? 'text-red-400'
                          : activeStep.riskLevel === 'HIGH'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }
                    >
                      {activeStep.riskLevel || 'LOW'}
                    </span>
                    <span className="text-[0.65rem] font-mono text-gray-400">
                      Trust: {activeStep.sourceTrustLevel || 'TRUSTED'}
                    </span>
                  </div>
                  <div className="text-[0.65rem] text-[var(--color-text-muted)] mt-1.5 truncate">
                    Source: {activeStep.source || 'AGENT_PLAN'}
                  </div>
                </div>
              </div>

              {/* Multidimensional Blast Radius Breakdown */}
              {activeStep.blastRadius && (
                <div className="p-4 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)] space-y-2.5">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-extrabold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                      <Lock size={13} />
                      Multidimensional Blast Radius Surface
                    </h4>
                    <span className="text-[0.65rem] font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-300 font-bold border border-red-500/40">
                      Impact: {activeStep.blastRadius.blastRadiusLevel || 'CRITICAL'} ({activeStep.blastRadius.blastRadiusScore || 85}%)
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)]/50">
                      <span className="text-[0.65rem] text-[var(--color-text-muted)] block">Files Affected</span>
                      <span className="font-mono text-amber-300 text-[0.7rem] truncate block mt-0.5">
                        {activeStep.blastRadius.filesAffected?.length > 0
                          ? activeStep.blastRadius.filesAffected.join(', ')
                          : 'None'}
                      </span>
                    </div>

                    <div className="p-2 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)]/50">
                      <span className="text-[0.65rem] text-[var(--color-text-muted)] block">Database Objects</span>
                      <span className="font-mono text-cyan-300 text-[0.7rem] truncate block mt-0.5">
                        {activeStep.blastRadius.databaseObjectsAffected?.length > 0
                          ? activeStep.blastRadius.databaseObjectsAffected.join(', ')
                          : 'None'}
                      </span>
                    </div>

                    <div className="p-2 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)]/50">
                      <span className="text-[0.65rem] text-[var(--color-text-muted)] block">Network Dests</span>
                      <span className="font-mono text-emerald-300 text-[0.7rem] truncate block mt-0.5">
                        {activeStep.blastRadius.networkDestinations?.length > 0
                          ? activeStep.blastRadius.networkDestinations.join(', ')
                          : 'None'}
                      </span>
                    </div>

                    <div className="p-2 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)]/50">
                      <span className="text-[0.65rem] text-[var(--color-text-muted)] block">Privileges Required</span>
                      <span className="font-mono text-red-300 text-[0.7rem] truncate block mt-0.5">
                        {activeStep.blastRadius.privilegesRequired || 'STANDARD_USER'}
                      </span>
                    </div>
                  </div>

                  <p className="text-[0.7rem] text-[var(--color-text-muted)] leading-relaxed">
                    {activeStep.blastRadius.summary}
                  </p>
                </div>
              )}

              {/* Step Payload & Execution Detail */}
              <div className="p-4 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)] space-y-2 text-xs">
                <div className="flex items-start gap-2">
                  <span className="text-[var(--color-text-muted)] font-bold shrink-0 w-24">Description:</span>
                  <span className="text-white font-medium">{activeStep.description || 'N/A'}</span>
                </div>

                {activeStep.target && (
                  <div className="flex items-start gap-2">
                    <span className="text-[var(--color-text-muted)] font-bold shrink-0 w-24">Target:</span>
                    <span className="font-mono text-amber-300 bg-amber-950/30 px-2 py-0.5 rounded border border-amber-500/30 truncate">
                      {activeStep.target}
                    </span>
                  </div>
                )}

                {activeStep.reason && (
                  <div className="flex items-start gap-2 pt-1 border-t border-[var(--color-border)]/40">
                    <span className="text-[var(--color-text-muted)] font-bold shrink-0 w-24">Gateway Reason:</span>
                    <span className="text-gray-300 leading-relaxed font-mono text-[0.7rem]">
                      {activeStep.reason}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-bg-primary)] flex items-center justify-between">
          <span className="text-xs text-[var(--color-text-muted)] font-mono">
            Agent Guard Replay Engine &bull; Cryptographically auditable trace
          </span>
          <button
            onClick={onClose}
            className="btn-secondary py-1.5 px-4 text-xs font-bold text-gray-300 hover:text-white"
          >
            Close Replay
          </button>
        </div>
      </div>
    </div>
  );
}
