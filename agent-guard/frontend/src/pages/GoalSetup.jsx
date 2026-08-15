import { useState } from 'react';
import { Shield, Plus, X, Lock, ChevronRight, Cpu, Layers, Radio, Zap } from 'lucide-react';
import Header from '../components/Header';
import ConnectedAgentCard from '../components/ConnectedAgentCard';
import ConnectIdeModal from '../components/ConnectIdeModal';
import { analyzeGoal } from '../services/api';

/**
 * GoalSetup — Home / Setup page for Agent Guard.
 * Features prominent [+ CONNECT IDE] integration and dynamic policy formulation.
 */
export default function GoalSetup({ onStart, sessionStatus, onStatusChange }) {
  const [userGoal, setUserGoal] = useState(
    'Create a portfolio website using React with a dark theme. Do not modify the backend.'
  );
  const [constraints, setConstraints] = useState([
    'Do not modify backend',
    'Do not access secrets',
  ]);
  const [newConstraint, setNewConstraint] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [goalPolicy, setGoalPolicy] = useState(null);
  const [connectModalOpen, setConnectModalOpen] = useState(false);

  const addConstraint = () => {
    const trimmed = newConstraint.trim();
    if (trimmed && !constraints.includes(trimmed)) {
      setConstraints([...constraints, trimmed]);
      setNewConstraint('');
    }
  };

  const removeConstraint = (idx) => {
    setConstraints(constraints.filter((_, i) => i !== idx));
  };

  const handleAnalyze = async () => {
    if (!userGoal.trim()) return;
    setAnalyzing(true);
    try {
      const res = await analyzeGoal(userGoal, constraints);
      setGoalPolicy(res.goalPolicy);
    } catch (err) {
      console.error('Goal analysis failed:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAcceptAndStart = async () => {
    setLoading(true);
    try {
      await onStart(userGoal, constraints, false, null, goalPolicy, false);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptAndMonitor = async () => {
    setLoading(true);
    try {
      await onStart(userGoal, constraints, false, null, goalPolicy, true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        agentStatus="IDLE"
        sessionStatus={sessionStatus}
        onOpenConnectModal={() => setConnectModalOpen(true)}
      />

      <main className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="w-full max-w-3xl animate-fade-in-up space-y-6">
          {/* Hero */}
          <div className="text-center">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mx-auto mb-3 shadow-lg shadow-blue-500/25 animate-pulse-glow">
              <Shield size={28} className="text-white" />
            </div>
            <h2 className="text-2xl font-bold text-[var(--color-text-primary)] mb-1">
              Agent Guard — Runtime Security Gateway
            </h2>
            <p className="text-xs text-[var(--color-text-secondary)] max-w-lg mx-auto leading-relaxed">
              Agent Guard protects the actions of your connected AI agent with real-time goal integrity, dynamic policy generation, and PreToolUse authorization.
            </p>
          </div>

          {/* Connected Agent Quick Status / Connect Card */}
          <ConnectedAgentCard
            status={sessionStatus}
            onOpenConnectModal={() => setConnectModalOpen(true)}
            onStatusChange={onStatusChange}
          />

          {/* Form Card */}
          <div className="glass-card p-6 space-y-5">

            {/* Goal Input */}
            <div>
              <label className="text-[0.7rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold mb-2 block">
                User Natural-Language Goal
              </label>
              <textarea
                value={userGoal}
                onChange={(e) => {
                  setUserGoal(e.target.value);
                  setGoalPolicy(null);
                }}
                rows={3}
                className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 resize-none transition-colors font-sans"
                placeholder="Describe what the AI agent should accomplish..."
              />
            </div>

            {/* Constraints */}
            <div>
              <label className="text-[0.7rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold mb-2 block">
                Explicit Constraints
              </label>

              <div className="flex flex-wrap gap-2 mb-3">
                {constraints.map((c, i) => (
                  <span
                    key={i}
                    className="flex items-center gap-1.5 text-[0.7rem] px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  >
                    <Lock size={11} />
                    {c}
                    <button
                      onClick={() => removeConstraint(i)}
                      className="ml-1 text-amber-400/60 hover:text-amber-300 transition-colors"
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={newConstraint}
                  onChange={(e) => setNewConstraint(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addConstraint()}
                  className="flex-1 bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-xs text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="Add a constraint..."
                />
                <button
                  onClick={addConstraint}
                  className="px-3 py-2 rounded-lg border border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-blue-500 hover:text-blue-400 transition-colors"
                >
                  <Plus size={16} />
                </button>
              </div>
            </div>

            {/* Action Buttons before policy generation */}
            {!goalPolicy && (
              <div className="space-y-2.5">
                {/* Direct 1-Click Antigravity Monitor Start */}
                <button
                  onClick={handleAcceptAndMonitor}
                  disabled={loading || !userGoal.trim()}
                  className="btn-primary w-full flex items-center justify-center gap-2 py-3.5 text-sm font-bold tracking-wide shadow-lg shadow-blue-500/20 disabled:opacity-50"
                  style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
                >
                  {loading ? (
                    'Activating Monitor...'
                  ) : (
                    <>
                      <Radio size={18} className="animate-pulse" />
                      START ANTIGRAVITY MONITOR
                    </>
                  )}
                </button>

                {/* Optional Deep Policy Analysis */}
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing || !userGoal.trim()}
                  className="btn-secondary w-full flex items-center justify-center gap-2 py-2.5 text-xs text-[var(--color-text-secondary)] hover:text-white border border-[var(--color-border)] hover:border-blue-500/50 disabled:opacity-50 transition-colors"
                >
                  {analyzing ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Analyzing Security Policy...
                    </>
                  ) : (
                    <>
                      <Cpu size={14} />
                      Preview Dynamic Security Policy Boundaries
                      <ChevronRight size={13} />
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Step 2: System Understanding / Human Confirmation Card */}
            {goalPolicy && (
              <div className="p-4 rounded-xl bg-blue-950/30 border border-blue-500/30 space-y-3 animate-fade-in-up">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                    <Layers size={14} />
                    System Policy Understanding
                  </span>
                  <span className="text-[0.65rem] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold uppercase">
                    {goalPolicy.domain || 'General Task'}
                  </span>
                </div>

                <div className="text-xs text-[var(--color-text-secondary)]">
                  <span className="font-semibold text-white">Objective:</span> {goalPolicy.objective}
                </div>

                {/* Allowed Scope */}
                <div>
                  <span className="text-[0.65rem] font-semibold text-emerald-400 uppercase tracking-wider block mb-1">
                    Allowed Scope
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {(goalPolicy.allowedScope || []).map((scope, idx) => (
                      <span key={idx} className="text-[0.65rem] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                        ✓ {scope}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Restricted Scope */}
                {goalPolicy.restrictedScope && goalPolicy.restrictedScope.length > 0 && (
                  <div>
                    <span className="text-[0.65rem] font-semibold text-red-400 uppercase tracking-wider block mb-1">
                      Restricted Scope
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {goalPolicy.restrictedScope.map((scope, idx) => (
                        <span key={idx} className="text-[0.65rem] px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                          🚫 {scope}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Confirmation Buttons */}
                <div className="grid grid-cols-1 gap-3 pt-2">
                  {/* Antigravity Monitor Mode — Primary */}
                  <button
                    onClick={handleAcceptAndMonitor}
                    disabled={loading}
                    className="btn-primary flex items-center justify-center gap-2 py-3 text-xs"
                    style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
                  >
                    {loading ? (
                      'Activating Monitor...'
                    ) : (
                      <>
                        <Radio size={15} />
                        ACCEPT & MONITOR (ANTIGRAVITY)
                      </>
                    )}
                  </button>

                  <div className="grid grid-cols-2 gap-3">
                    {/* OpenAI Agent Mode — Secondary */}
                    <button
                      onClick={handleAcceptAndStart}
                      disabled={loading}
                      className="btn-primary flex items-center justify-center gap-2 py-2.5 text-xs bg-emerald-600 hover:bg-emerald-500"
                    >
                      {loading ? (
                        'Starting Agent...'
                      ) : (
                        <>
                          <Zap size={14} />
                          START OPENAI AGENT
                        </>
                      )}
                    </button>

                    <button
                      onClick={() => setGoalPolicy(null)}
                      className="btn-secondary py-2.5 text-xs text-[var(--color-text-muted)]"
                    >
                      EDIT GOAL
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          <p className="text-center text-[0.65rem] text-[var(--color-text-muted)] mt-4">
            Agent Guard protects the actions of your connected AI agent.
          </p>
        </div>
      </main>

      {/* Connect IDE Modal */}
      <ConnectIdeModal
        isOpen={connectModalOpen}
        onClose={() => setConnectModalOpen(false)}
        initialStatus={sessionStatus}
        onStatusChange={onStatusChange}
      />
    </div>
  );
}

