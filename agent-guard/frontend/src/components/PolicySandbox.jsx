import { useState } from 'react';
import {
  FlaskConical,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Cpu,
  FileCode,
  Terminal,
  Database,
  Trash2,
  Key,
  Globe,
  Sparkles,
  RefreshCw,
  Info,
} from 'lucide-react';
import { evaluatePolicyAction } from '../services/api';

/**
 * PolicySandbox — Interactive Tool Evaluator & Policy Playground.
 * Allows security engineers and developers to evaluate hypothetical tool actions
 * against the active Goal Policy in real time to verify authorization boundaries.
 */
export default function PolicySandbox({ goalId }) {
  const [actionType, setActionType] = useState('FILE_WRITE');
  const [target, setTarget] = useState('src/components/Hero.jsx');
  const [description, setDescription] = useState('Create responsive Hero banner component with CTA buttons');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const toolTypes = [
    { value: 'FILE_WRITE', label: 'FILE_WRITE (Create/Modify File)', icon: FileCode },
    { value: 'COMMAND_EXECUTION', label: 'COMMAND_EXECUTION (Shell Command)', icon: Terminal },
    { value: 'READ_FILE', label: 'READ_FILE (Read File Content)', icon: FileCode },
    { value: 'DELETE_FILE', label: 'DELETE_FILE (Delete File)', icon: Trash2 },
    { value: 'DATABASE_QUERY', label: 'DATABASE_QUERY (Database Operations)', icon: Database },
    { value: 'ACCESS_SECRET', label: 'ACCESS_SECRET (Environment Secrets)', icon: Key },
    { value: 'EXTERNAL_HTTP', label: 'EXTERNAL_HTTP (Outbound Network Call)', icon: Globe },
  ];

  const presets = [
    {
      label: '🟢 Safe Component Creation',
      actionType: 'FILE_WRITE',
      target: 'src/components/PricingCard.jsx',
      description: 'Implement frontend pricing tier cards with Tailwind styling',
    },
    {
      label: '🟢 Run Unit Tests',
      actionType: 'COMMAND_EXECUTION',
      target: 'npm test -- --coverage',
      description: 'Run frontend test suite to verify component rendering',
    },
    {
      label: '🟡 Modify Backend Controller',
      actionType: 'FILE_WRITE',
      target: 'backend/app/controllers/user.py',
      description: 'Add server-side user authentication endpoint',
    },
    {
      label: '🔴 Access Production Secrets',
      actionType: 'ACCESS_SECRET',
      target: '.env.production',
      description: 'Read database connection string and stripe secret key',
    },
    {
      label: '🔴 Destructive System Wipe',
      actionType: 'COMMAND_EXECUTION',
      target: 'rm -rf / --no-preserve-root',
      description: 'Purge host root filesystem and system binaries',
    },
  ];

  const applyPreset = (preset) => {
    setActionType(preset.actionType);
    setTarget(preset.target);
    setDescription(preset.description);
  };

  const handleEvaluate = async () => {
    if (!target.trim()) return;
    setLoading(true);
    try {
      const res = await evaluatePolicyAction(
        goalId,
        actionType,
        target.trim(),
        description.trim()
      );
      setResult(res);
      setHistory((prev) => [res, ...prev.slice(0, 9)]);
    } catch (err) {
      console.error('Policy evaluation failed:', err);
      // Client-side fallback evaluator
      const isDangerous =
        target.includes('.env') ||
        target.includes('rm -rf') ||
        target.includes('shadow') ||
        target.includes('password');
      const isBackend = target.includes('backend') || target.includes('database');

      const fallback = {
        evaluationId: `EVAL-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
        actionType,
        target,
        description,
        decision: isDangerous ? 'BLOCK' : isBackend ? 'REQUIRE_APPROVAL' : 'ALLOW',
        executionStatus: 'NOT_EXECUTED',
        goalAlignmentScore: isDangerous ? 0 : isBackend ? 55 : 95,
        alignmentStatus: isDangerous ? 'UNALIGNED' : isBackend ? 'BORDERLINE' : 'ALIGNED',
        riskLevel: isDangerous ? 'CRITICAL' : isBackend ? 'HIGH' : 'LOW',
        riskScore: isDangerous ? 95 : isBackend ? 60 : 15,
        driftScore: isDangerous ? 90 : isBackend ? 50 : 5,
        driftLevel: isDangerous ? 'CRITICAL' : isBackend ? 'MODERATE' : 'NORMAL',
        actionClassification: isDangerous ? 'DANGEROUS' : isBackend ? 'UNCERTAIN' : 'PRODUCTIVE',
        reason: isDangerous
          ? 'Attempted access to protected secrets or destructive command.'
          : isBackend
          ? 'Modifies backend resources outside permitted frontend scope.'
          : 'Action is well aligned with current frontend goal policy.',
        violatedConstraints: isDangerous ? ['Forbidden Secret / System Constraint'] : [],
        timestamp: new Date().toISOString(),
      };
      setResult(fallback);
      setHistory((prev) => [fallback, ...prev.slice(0, 9)]);
    } finally {
      setLoading(false);
    }
  };

  const getDecisionBadge = (decision) => {
    if (decision === 'ALLOW' || decision === 'APPROVED') {
      return {
        bg: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
        icon: CheckCircle2,
        label: 'ALLOW ACTION',
      };
    }
    if (decision === 'REQUIRE_APPROVAL') {
      return {
        bg: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
        icon: AlertTriangle,
        label: 'REQUIRE APPROVAL',
      };
    }
    return {
      bg: 'bg-red-500/15 text-red-400 border-red-500/30',
      icon: XCircle,
      label: 'BLOCK ACTION',
    };
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header Banner */}
      <div className="glass-card p-6 bg-gradient-to-r from-blue-950/40 via-[var(--color-bg-card)] to-cyan-950/30 border border-blue-500/30">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/25">
              <FlaskConical size={26} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  Policy Sandbox & Tool Evaluator
                </h2>
                <span className="text-[0.65rem] font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 uppercase">
                  Zero-Side-Effects Lab
                </span>
              </div>
              <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">
                Simulate arbitrary agent tool calls against the active Goal Policy to preview authorization verdicts, alignment scores, and risk escalations.
              </p>
            </div>
          </div>

          <span className="text-xs font-mono text-[var(--color-text-muted)] bg-[var(--color-bg-primary)] px-3 py-1.5 rounded-lg border border-[var(--color-border)]">
            Policy Scope: {goalId || 'G-ACTIVE-SESSION'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Action Form & Preset Selectors */}
        <div className="lg:col-span-6 space-y-4">
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-primary)] flex items-center gap-2">
                <Cpu size={15} className="text-cyan-400" />
                Build Proposed Tool Action
              </span>
              <span className="text-[0.65rem] text-[var(--color-text-muted)]">
                PreToolUse Simulation
              </span>
            </div>

            {/* Presets Chips */}
            <div>
              <span className="text-[0.65rem] text-[var(--color-text-muted)] uppercase tracking-wider font-semibold block mb-2">
                Quick-Test Scenarios:
              </span>
              <div className="flex flex-wrap gap-2">
                {presets.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => applyPreset(p)}
                    className="text-[0.7rem] px-2.5 py-1 rounded-lg bg-[var(--color-bg-primary)] border border-[var(--color-border)] hover:border-cyan-500/50 text-[var(--color-text-secondary)] hover:text-white transition-colors"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Tool Action Type */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[var(--color-text-secondary)]">
                Action Type / Tool Call
              </label>
              <select
                value={actionType}
                onChange={(e) => setActionType(e.target.value)}
                className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-xl px-3.5 py-2.5 text-xs text-[var(--color-text-primary)] focus:outline-none focus:border-cyan-500 font-mono"
              >
                {toolTypes.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Target Path or Command */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[var(--color-text-secondary)]">
                Target Resource / Command / Path
              </label>
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="e.g. src/components/Hero.jsx or npm run build"
                className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-xl px-3.5 py-2.5 text-xs text-[var(--color-text-primary)] focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>

            {/* Description / Intent */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[var(--color-text-secondary)]">
                Action Intent / Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="Describe the agent's intent or reasoning behind this action..."
                className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-xl px-3.5 py-2.5 text-xs text-[var(--color-text-primary)] focus:outline-none focus:border-cyan-500 resize-none font-sans"
              />
            </div>

            <button
              onClick={handleEvaluate}
              disabled={loading || !target.trim()}
              className="btn-primary w-full flex items-center justify-center gap-2 py-3 text-xs font-bold shadow-lg shadow-cyan-500/20 disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
            >
              {loading ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  Evaluating Policy Engine...
                </>
              ) : (
                <>
                  <Play size={14} fill="currentColor" />
                  EVALUATE TOOL ACTION
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Real-time Evaluation Results */}
        <div className="lg:col-span-6 space-y-4">
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-primary)] flex items-center gap-2">
                <Sparkles size={15} className="text-cyan-400" />
                Security Gateway Evaluation Result
              </span>
              {result && (
                <span className="text-[0.65rem] font-mono text-[var(--color-text-muted)]">
                  {result.evaluationId}
                </span>
              )}
            </div>

            {loading ? (
              <div className="p-12 text-center space-y-3 bg-[var(--color-bg-primary)]/50 rounded-xl border border-[var(--color-border)]">
                <div className="w-9 h-9 border-3 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mx-auto" />
                <p className="text-xs font-bold text-cyan-400 animate-pulse">
                  Synthesizing multi-step drift and risk boundaries...
                </p>
              </div>
            ) : result ? (
              <div className="space-y-4 bg-[var(--color-bg-primary)] p-4 rounded-xl border border-[var(--color-border)] animate-fade-in-up">
                {/* Decision Badge Card */}
                {(() => {
                  const badge = getDecisionBadge(result.decision);
                  const BadgeIcon = badge.icon;
                  return (
                    <div
                      className={`p-3.5 rounded-xl border flex items-center justify-between gap-3 ${badge.bg}`}
                    >
                      <div className="flex items-center gap-2.5">
                        <BadgeIcon size={22} className="shrink-0" />
                        <div>
                          <span className="text-xs font-extrabold block">
                            {badge.label}
                          </span>
                          <span className="text-[0.65rem] opacity-80">
                            Classification: {result.actionClassification || 'EVALUATED'}
                          </span>
                        </div>
                      </div>
                      <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-black/20 uppercase">
                        {result.decision}
                      </span>
                    </div>
                  );
                })()}

                {/* 4 Metric Telemetry Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div className="p-2.5 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)] text-center">
                    <span className="text-[0.6rem] text-[var(--color-text-muted)] uppercase block">
                      Alignment
                    </span>
                    <span className="text-sm font-bold text-cyan-400">
                      {result.goalAlignmentScore}%
                    </span>
                    <span className="text-[0.55rem] text-[var(--color-text-muted)] block">
                      {result.alignmentStatus}
                    </span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)] text-center">
                    <span className="text-[0.6rem] text-[var(--color-text-muted)] uppercase block">
                      Action Risk
                    </span>
                    <span className="text-sm font-bold text-amber-400">
                      {result.riskLevel}
                    </span>
                    <span className="text-[0.55rem] text-[var(--color-text-muted)] block">
                      Score: {result.riskScore}%
                    </span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)] text-center">
                    <span className="text-[0.6rem] text-[var(--color-text-muted)] uppercase block">
                      Goal Drift
                    </span>
                    <span className="text-sm font-bold text-purple-400">
                      {result.driftLevel || 'NORMAL'}
                    </span>
                    <span className="text-[0.55rem] text-[var(--color-text-muted)] block">
                      Drift: {result.driftScore}%
                    </span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)] text-center">
                    <span className="text-[0.6rem] text-[var(--color-text-muted)] uppercase block">
                      Host Impact
                    </span>
                    <span className="text-sm font-bold text-emerald-400">
                      SAFE
                    </span>
                    <span className="text-[0.55rem] text-[var(--color-text-muted)] block">
                      Sandbox Only
                    </span>
                  </div>
                </div>

                {/* Constraint Violations (if any) */}
                {result.violatedConstraints && result.violatedConstraints.length > 0 && (
                  <div className="p-2.5 rounded-lg bg-red-950/20 border border-red-500/30 text-xs">
                    <span className="text-[0.65rem] font-bold text-red-400 uppercase block mb-1">
                      ⚠️ Violated Constraints:
                    </span>
                    <ul className="list-disc list-inside text-red-300 text-[0.7rem] space-y-0.5">
                      {result.violatedConstraints.map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Explainable Decision Narrative */}
                <div className="p-3 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)] space-y-1">
                  <span className="text-[0.65rem] font-bold uppercase tracking-wider text-cyan-400 block">
                    Security Gateway Verdict Explanation:
                  </span>
                  <p className="text-xs text-[var(--color-text-secondary)] italic leading-relaxed">
                    "{result.reason}"
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-10 text-center bg-[var(--color-bg-primary)]/50 rounded-xl border border-[var(--color-border)]">
                <Info size={32} className="text-cyan-400 mx-auto mb-2 opacity-70" />
                <h4 className="text-xs font-bold text-[var(--color-text-primary)]">
                  Sandbox Awaiting Input
                </h4>
                <p className="text-[0.7rem] text-[var(--color-text-muted)] mt-1 max-w-xs mx-auto">
                  Configure an action on the left or select a preset, then click 'Evaluate Tool Action'.
                </p>
              </div>
            )}
          </div>

          {/* Evaluation History Feed */}
          {history.length > 0 && (
            <div className="glass-card p-4 space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-primary)] block mb-2">
                Recent Sandbox Invocations ({history.length})
              </span>
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {history.map((h, i) => (
                  <div
                    key={i}
                    onClick={() => setResult(h)}
                    className="p-2 rounded-lg bg-[var(--color-bg-primary)] border border-[var(--color-border)] hover:border-cyan-500/40 cursor-pointer flex items-center justify-between text-xs transition-colors"
                  >
                    <div className="truncate">
                      <span className="font-mono text-cyan-300 font-semibold block truncate">
                        {h.actionType} {h.target}
                      </span>
                      <span className="text-[0.65rem] text-[var(--color-text-muted)] truncate block">
                        {h.description}
                      </span>
                    </div>
                    <span
                      className={`text-[0.6rem] font-bold px-2 py-0.5 rounded border uppercase shrink-0 ${
                        h.decision === 'ALLOW'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : h.decision === 'REQUIRE_APPROVAL'
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-red-500/10 text-red-400 border-red-500/30'
                      }`}
                    >
                      {h.decision}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
