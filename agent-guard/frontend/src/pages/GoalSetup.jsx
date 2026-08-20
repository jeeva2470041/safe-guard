import { useState } from 'react';
import {
  Shield,
  ChevronRight,
  Cpu,
  Layers,
  Radio,
  Zap,
  Sparkles,
  Play,
  Flame,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import Header from '../components/Header';
import ConnectedAgentCard from '../components/ConnectedAgentCard';
import ConnectIdeModal from '../components/ConnectIdeModal';
import { analyzeGoal } from '../services/api';

/**
 * GoalSetup — Setup and Quick-Start Launchpad for Agent Guard.
 * Includes natural language prompt synthesis, preset scenario decks, and dynamic policy confirmation.
 */
export default function GoalSetup({ onStart, sessionStatus, onStatusChange }) {
  const [userGoal, setUserGoal] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [goalPolicy, setGoalPolicy] = useState(null);
  const [connectModalOpen, setConnectModalOpen] = useState(false);

  const promptTemplates = [
    {
      label: '✈️ Flight Booking',
      prompt: 'Book the cheapest flight from Chennai to Delhi tomorrow.',
    },
    {
      label: '🏨 Hotel Reservation',
      prompt: 'Book a 4-star hotel in Mumbai for next weekend.',
    },
    {
      label: '🛍️ Amazon Shopping',
      prompt: 'Buy Sony noise-cancelling headphones on Amazon under $300.',
    },
    {
      label: '📧 Email Report',
      prompt: 'Send the quarterly sales report to manager@company.com',
    },
    {
      label: '⚛️ React Portfolio App',
      prompt: 'Create a modern portfolio website using React and Tailwind CSS with a dark theme. Do not modify the backend or database.',
    },
  ];

  const scenarios = [
    {
      id: 'scenario-1',
      title: 'Scenario 1: Normal Flow',
      badge: 'HIGH INTEGRITY',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      icon: CheckCircle2,
      iconColor: 'text-emerald-400',
      description: 'Agent creates components, styles CSS, and runs tests within permitted frontend scope. All actions pass.',
    },
    {
      id: 'scenario-2',
      title: 'Scenario 2: Goal Drift',
      badge: 'DRIFT INTERVENTION',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      icon: AlertTriangle,
      iconColor: 'text-amber-400',
      description: 'Agent begins safely, then gradually drifts into editing server.js and database.sql, triggering automatic pause.',
    },
    {
      id: 'scenario-3',
      title: 'Scenario 3: Red Team Breach',
      badge: 'CRITICAL BLOCK',
      badgeColor: 'bg-red-500/10 text-red-400 border-red-500/30',
      icon: Flame,
      iconColor: 'text-red-400',
      description: 'Adversarial prompt injection attempts .env exfiltration and database deletion, blocked immediately with 100% risk score.',
    },
  ];

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

  const handleLaunchScenario = async (scenarioId) => {
    setLoading(true);
    try {
      await onStart('', [], false, scenarioId, null, false);
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
        showNav={false}
      />

      <main className="flex-1 max-w-[1140px] mx-auto w-full px-3.5 sm:px-6 py-6 sm:py-8 space-y-6 sm:space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center mx-auto shadow-lg shadow-cyan-500/25 animate-pulse-glow">
            <Shield size={26} className="text-white sm:w-7 sm:h-7" />
          </div>
          <h2 className="text-xl sm:text-3xl font-extrabold text-[var(--color-text-primary)] tracking-tight">
            Agent Guard Security Operations Center
          </h2>
          <p className="text-xs sm:text-sm text-[var(--color-text-secondary)] max-w-xl mx-auto leading-relaxed">
            Real-time goal integrity, dynamic policy generation, and PreToolUse action authorization for autonomous AI coding agents.
          </p>
        </div>

        {/* Connected Agent Status Banner */}
        <ConnectedAgentCard
          status={sessionStatus}
          onOpenConnectModal={() => setConnectModalOpen(true)}
          onStatusChange={onStatusChange}
        />

        {/* 1-Click Quick-Start Scenario Deck */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-primary)] flex items-center gap-1.5">
              <Zap size={14} className="text-amber-400 shrink-0" />
              1-Click Interactive Test Scenarios
            </span>
            <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)]">
              Simulate pre-configured agent runs
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
            {scenarios.map((sc) => {
              const Icon = sc.icon;
              return (
                <div
                  key={sc.id}
                  className="glass-card p-4 flex flex-col justify-between space-y-3 border hover:border-cyan-500/40 transition-all duration-200"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <Icon size={16} className={`${sc.iconColor} shrink-0`} />
                        <h4 className="text-xs font-bold text-[var(--color-text-primary)] truncate">
                          {sc.title}
                        </h4>
                      </div>
                      <span className={`text-[0.55rem] sm:text-[0.6rem] font-bold px-2 py-0.5 rounded border uppercase shrink-0 ${sc.badgeColor}`}>
                        {sc.badge}
                      </span>
                    </div>
                    <p className="text-[0.65rem] sm:text-[0.7rem] text-[var(--color-text-secondary)] leading-relaxed">
                      {sc.description}
                    </p>
                  </div>

                  <button
                    onClick={() => handleLaunchScenario(sc.id)}
                    disabled={loading}
                    className="btn-secondary w-full py-2 text-xs font-semibold flex items-center justify-center gap-1.5 hover:bg-cyan-500/10 hover:text-cyan-300 hover:border-cyan-500/40"
                  >
                    <Play size={11} fill="currentColor" />
                    Launch {sc.title}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Custom Goal Prompt Builder */}
        <div className="glass-card p-4 sm:p-6 space-y-4 sm:space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
            <label className="text-xs uppercase tracking-wider text-[var(--color-text-primary)] font-bold flex items-center gap-1.5">
              <Sparkles size={14} className="text-cyan-400 shrink-0" />
              Enter Custom AI Agent Goal & Security Instructions
            </label>
            <span className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)]">
              Dynamic policy synthesized on submit
            </span>
          </div>

          {/* Quick-Prompt Templates */}
          <div className="flex flex-wrap gap-1.5 sm:gap-2">
            {promptTemplates.map((tpl, i) => (
              <button
                key={i}
                onClick={() => {
                  setUserGoal(tpl.prompt);
                  setGoalPolicy(null);
                }}
                className="text-[0.65rem] sm:text-[0.7rem] px-2.5 py-1 rounded-lg bg-[var(--color-bg-primary)] border border-[var(--color-border)] hover:border-cyan-500/50 text-[var(--color-text-secondary)] hover:text-white transition-colors"
              >
                {tpl.label}
              </button>
            ))}
          </div>

          <textarea
            value={userGoal}
            onChange={(e) => {
              setUserGoal(e.target.value);
              setGoalPolicy(null);
            }}
            rows={4}
            className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-xl px-3.5 py-2.5 sm:px-4 sm:py-3 text-xs sm:text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 resize-none transition-all font-sans leading-relaxed shadow-inner"
            placeholder="Enter your prompt for the AI agent (e.g., Create a responsive dashboard using React. Do not touch backend database or modify secrets)..."
          />

          {/* Actions before policy analysis */}
          {!goalPolicy && (
            <div className="space-y-2.5">
              <button
                onClick={handleAcceptAndMonitor}
                disabled={loading || !userGoal.trim()}
                className="btn-primary w-full flex items-center justify-center gap-2 py-3 sm:py-3.5 text-xs font-bold tracking-wider shadow-lg shadow-cyan-500/20 disabled:opacity-50"
                style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
              >
                {loading ? (
                  'Activating Security Gateway...'
                ) : (
                  <>
                    <Radio size={15} className="animate-pulse" />
                    ACTIVATE GOOGLE ANTIGRAVITY MONITOR
                  </>
                )}
              </button>

              <button
                onClick={handleAnalyze}
                disabled={analyzing || !userGoal.trim()}
                className="btn-secondary w-full flex items-center justify-center gap-2 py-2.5 text-xs text-[var(--color-text-secondary)] hover:text-white border border-[var(--color-border)] hover:border-cyan-500/50 disabled:opacity-50"
              >
                {analyzing ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Synthesizing Dynamic Security Boundaries...
                  </>
                ) : (
                  <>
                    <Cpu size={14} />
                    Preview Dynamic Goal Policy & Scope Boundaries
                    <ChevronRight size={13} />
                  </>
                )}
              </button>
            </div>
          )}

          {/* Synthesized Policy Confirmation Card */}
          {goalPolicy && (
            <div className="p-3.5 sm:p-4 rounded-xl bg-blue-950/30 border border-cyan-500/40 space-y-3 animate-fade-in-up">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                  <Layers size={14} />
                  Synthesized Security Policy
                </span>
                <span className="text-[0.6rem] sm:text-[0.65rem] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold uppercase">
                  {goalPolicy.domain || 'Frontend Application'}
                </span>
              </div>

              <div className="text-xs text-[var(--color-text-secondary)] break-words">
                <span className="font-semibold text-white">Objective:</span> {goalPolicy.objective}
              </div>

              {/* Allowed Scope */}
              <div>
                <span className="text-[0.6rem] sm:text-[0.65rem] font-semibold text-emerald-400 uppercase tracking-wider block mb-1">
                  Allowed Modification Scope:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {(goalPolicy.allowedScope || []).map((scope, idx) => (
                    <span
                      key={idx}
                      className="text-[0.6rem] sm:text-[0.65rem] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-mono"
                    >
                      ✓ {scope}
                    </span>
                  ))}
                </div>
              </div>

              {/* Restricted Scope */}
              {goalPolicy.restrictedScope && goalPolicy.restrictedScope.length > 0 && (
                <div>
                  <span className="text-[0.6rem] sm:text-[0.65rem] font-semibold text-red-400 uppercase tracking-wider block mb-1">
                    Forbidden Scope Boundaries:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {goalPolicy.restrictedScope.map((scope, idx) => (
                      <span
                        key={idx}
                        className="text-[0.6rem] sm:text-[0.65rem] px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-mono"
                      >
                        🚫 {scope}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Confirmation Buttons */}
              <div className="grid grid-cols-1 gap-2.5 sm:gap-3 pt-2">
                <button
                  onClick={handleAcceptAndMonitor}
                  disabled={loading}
                  className="btn-primary flex items-center justify-center gap-2 py-2.5 sm:py-3 text-xs font-bold"
                  style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
                >
                  {loading ? (
                    'Activating Monitor...'
                  ) : (
                    <>
                      <Radio size={14} />
                      ACCEPT POLICY & MONITOR ANTIGRAVITY
                    </>
                  )}
                </button>

                <div className="grid grid-cols-2 gap-2 sm:gap-3">
                  <button
                    onClick={handleAcceptAndStart}
                    disabled={loading}
                    className="btn-primary flex items-center justify-center gap-1.5 sm:gap-2 py-2 sm:py-2.5 text-xs bg-emerald-600 hover:bg-emerald-500 border-none font-semibold"
                  >
                    <Zap size={13} />
                    START AGENT
                  </button>

                  <button
                    onClick={() => setGoalPolicy(null)}
                    className="btn-secondary py-2 sm:py-2.5 text-xs text-[var(--color-text-muted)] hover:text-white"
                  >
                    MODIFY
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <ConnectIdeModal
        isOpen={connectModalOpen}
        onClose={() => setConnectModalOpen(false)}
        initialStatus={sessionStatus}
        onStatusChange={onStatusChange}
      />
    </div>
  );
}
