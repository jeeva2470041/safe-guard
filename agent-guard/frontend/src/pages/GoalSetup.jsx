import { useState } from 'react';
import { Shield, ChevronRight, Cpu, Layers, Radio, Zap, Sparkles } from 'lucide-react';
import Header from '../components/Header';
import ConnectedAgentCard from '../components/ConnectedAgentCard';
import ConnectIdeModal from '../components/ConnectIdeModal';
import { analyzeGoal } from '../services/api';

/**
 * GoalSetup — Home / Setup page for Agent Guard.
 * Single unified prompt entry with dynamic security policy synthesis and PreToolUse authorization.
 */
export default function GoalSetup({ onStart, sessionStatus, onStatusChange }) {
  const [userGoal, setUserGoal] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [goalPolicy, setGoalPolicy] = useState(null);
  const [connectModalOpen, setConnectModalOpen] = useState(false);

  const handleAnalyze = async () => {
    if (!userGoal.trim()) return;
    setAnalyzing(true);
    try {
      const res = await analyzeGoal(userGoal.trim(), []);
      setGoalPolicy(res.goalPolicy);
    } catch (err) {
      console.error('Goal analysis failed:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAcceptAndStart = async () => {
    if (!userGoal.trim()) return;
    setLoading(true);
    try {
      await onStart(userGoal.trim(), [], false, null, goalPolicy, false);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptAndMonitor = async () => {
    if (!userGoal.trim()) return;
    setLoading(true);
    try {
      await onStart(userGoal.trim(), [], false, null, goalPolicy, true);
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

          {/* Prompt Entry Card */}
          <div className="glass-card p-6 space-y-5">
            {/* Prompt Input */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-[0.75rem] uppercase tracking-wider text-[var(--color-text-primary)] font-semibold flex items-center gap-1.5">
                  <Sparkles size={14} className="text-blue-400" />
                  Enter the Prompt
                </label>
                <span className="text-[0.65rem] text-[var(--color-text-muted)]">
                  Natural language goal & security instructions
                </span>
              </div>
              <textarea
                value={userGoal}
                onChange={(e) => {
                  setUserGoal(e.target.value);
                  setGoalPolicy(null);
                }}
                rows={4}
                className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-xl px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 resize-none transition-all font-sans leading-relaxed shadow-inner"
                placeholder="Enter the prompt for the AI agent (e.g., Create a portfolio website using React with a dark theme. Do not modify the backend)..."
                autoFocus
              />
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
                      EDIT PROMPT
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
