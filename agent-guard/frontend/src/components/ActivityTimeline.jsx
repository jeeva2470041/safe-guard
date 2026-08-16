import { useState, useMemo } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  FileText,
  Terminal,
  Trash2,
  Key,
  Edit,
  Play,
  Activity,
  Search,
  Filter,
  Layers,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react';

/**
 * ActivityTimeline — Live searchable and filterable timeline of agent actions
 * with status badges, alignment scores, risk levels, and 1-click HITL approval buttons.
 */
export default function ActivityTimeline({
  actions = [],
  onApprove,
  onReject,
  onSelectAction,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [verdictFilter, setVerdictFilter] = useState('ALL');
  const [riskFilter, setRiskFilter] = useState('ALL');

  const safeActions = Array.isArray(actions) ? actions : [];

  // Summary counts
  const stats = useMemo(() => {
    const total = safeActions.length;
    const allowed = safeActions.filter(
      (a) => a.decision === 'ALLOW' || a.decision === 'APPROVED' || a.executionStatus === 'EXECUTED'
    ).length;
    const blocked = safeActions.filter(
      (a) => a.decision === 'BLOCK' || a.decision === 'REJECTED' || a.executionStatus === 'NOT_EXECUTED'
    ).length;
    const pending = safeActions.filter(
      (a) => a.decision === 'REQUIRE_APPROVAL' && a.executionStatus === 'PENDING_APPROVAL'
    ).length;
    return { total, allowed, blocked, pending };
  }, [safeActions]);

  // Filtered action list
  const filteredActions = useMemo(() => {
    return safeActions.filter((action) => {
      // Verdict filter
      if (verdictFilter === 'ALLOW' && action.decision !== 'ALLOW' && action.decision !== 'APPROVED') {
        return false;
      }
      if (verdictFilter === 'BLOCK' && action.decision !== 'BLOCK' && action.decision !== 'REJECTED') {
        return false;
      }
      if (
        verdictFilter === 'PENDING' &&
        (action.decision !== 'REQUIRE_APPROVAL' || action.executionStatus !== 'PENDING_APPROVAL')
      ) {
        return false;
      }

      // Risk filter
      if (riskFilter !== 'ALL' && (action.riskLevel || 'LOW') !== riskFilter) {
        return false;
      }

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesTarget = (action.target || '').toLowerCase().includes(q);
        const matchesType = (action.actionType || '').toLowerCase().includes(q);
        const matchesDesc = (action.description || '').toLowerCase().includes(q);
        const matchesReason = (action.reason || '').toLowerCase().includes(q);
        return matchesTarget || matchesType || matchesDesc || matchesReason;
      }

      return true;
    });
  }, [safeActions, verdictFilter, riskFilter, searchQuery]);

  const getStatusIcon = (decision, executionStatus) => {
    if (decision === 'ALLOW' || decision === 'APPROVED' || executionStatus === 'EXECUTED') {
      return <CheckCircle2 size={18} className="text-emerald-400" />;
    }
    if (decision === 'REQUIRE_APPROVAL' && executionStatus === 'PENDING_APPROVAL') {
      return <AlertTriangle size={18} className="text-amber-400 animate-pulse" />;
    }
    if (decision === 'BLOCK' || decision === 'REJECTED' || executionStatus === 'NOT_EXECUTED') {
      return <XCircle size={18} className="text-red-400" />;
    }
    return <Clock size={18} className="text-gray-400" />;
  };

  const getStatusBadge = (decision, executionStatus) => {
    if (decision === 'APPROVED') return { class: 'status-badge-approved', text: 'APPROVED' };
    if (decision === 'REJECTED') return { class: 'status-badge-rejected', text: 'REJECTED' };
    if (decision === 'ALLOW') return { class: 'status-badge-allow', text: 'ALLOWED' };
    if (decision === 'REQUIRE_APPROVAL' && executionStatus === 'PENDING_APPROVAL') {
      return { class: 'status-badge-pending', text: 'REQUIRE APPROVAL' };
    }
    if (decision === 'BLOCK') return { class: 'status-badge-block', text: 'BLOCKED' };
    return { class: 'status-badge-allow', text: decision };
  };

  const getActionIcon = (actionType) => {
    const type = actionType?.toUpperCase();
    if (type === 'DELETE_FILE') return <Trash2 size={14} />;
    if (type === 'ACCESS_SECRET' || type === 'ACCESS_FILE' || type === 'ACCESS_ENV') return <Key size={14} />;
    if (type === 'MODIFY_FILE' || type === 'FILE_WRITE') return <Edit size={14} />;
    if (type === 'RUN_TESTS') return <Play size={14} />;
    if (type === 'RUN_COMMAND' || type === 'COMMAND_EXECUTION') return <Terminal size={14} />;
    return <FileText size={14} />;
  };

  const getRiskColor = (level) => {
    const colors = {
      LOW: 'text-emerald-400',
      MEDIUM: 'text-amber-400',
      HIGH: 'text-orange-400',
      CRITICAL: 'text-red-400',
    };
    return colors[level] || 'text-gray-400';
  };

  const formatTime = (ts) => {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return '';
    }
  };

  if (safeActions.length === 0) {
    return (
      <div className="glass-card p-8 text-center animate-fade-in-up space-y-3">
        <Clock size={36} className="text-[var(--color-text-muted)] mx-auto opacity-70" />
        <h4 className="text-sm font-bold text-[var(--color-text-primary)]">
          Awaiting Agent Actions
        </h4>
        <p className="text-xs text-[var(--color-text-muted)] max-w-sm mx-auto">
          Start a scenario or trigger an action in Antigravity to stream real-time PreToolUse security evaluations.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card p-5 animate-fade-in-up space-y-4">
      {/* Header & Stats Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-cyan-400" />
          <span className="text-xs font-bold tracking-wider uppercase text-[var(--color-text-primary)]">
            Live Security Interception Stream
          </span>
          <span className="text-[0.65rem] font-mono px-2 py-0.5 rounded bg-[var(--color-bg-primary)] border border-[var(--color-border)] text-cyan-300">
            {filteredActions.length} of {stats.total} actions
          </span>
        </div>

        {/* Quick Stats Pills */}
        <div className="flex items-center gap-2 text-[0.65rem] font-mono">
          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
            ✓ {stats.allowed} Allowed
          </span>
          <span className="px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-bold">
            ✕ {stats.blocked} Blocked
          </span>
          {stats.pending > 0 && (
            <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 font-bold animate-pulse">
              ⏳ {stats.pending} Approval
            </span>
          )}
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
        {/* Search Input */}
        <div className="md:col-span-6 relative">
          <Search size={14} className="absolute left-3 top-2.5 text-[var(--color-text-muted)]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search target path, tool, command, or explanation..."
            className="w-full pl-9 pr-3 py-1.5 bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg text-xs text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-cyan-500 font-sans"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-2 text-xs text-[var(--color-text-muted)] hover:text-white"
            >
              ✕
            </button>
          )}
        </div>

        {/* Verdict Filter Chips */}
        <div className="md:col-span-6 flex items-center gap-1.5 flex-wrap">
          {['ALL', 'ALLOW', 'BLOCK', 'PENDING'].map((v) => (
            <button
              key={v}
              onClick={() => setVerdictFilter(v)}
              className={`text-[0.65rem] px-2.5 py-1 rounded-md font-semibold transition-all ${
                verdictFilter === v
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'bg-[var(--color-bg-primary)] text-[var(--color-text-muted)] border border-[var(--color-border)] hover:text-white'
              }`}
            >
              {v === 'ALL' ? 'All Verdicts' : v}
            </button>
          ))}

          {/* Risk Level Filter Dropdown */}
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="text-[0.65rem] px-2 py-1 bg-[var(--color-bg-primary)] text-[var(--color-text-secondary)] border border-[var(--color-border)] rounded-md focus:outline-none ml-auto"
          >
            <option value="ALL">All Risk Levels</option>
            <option value="LOW">Low Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="HIGH">High Risk</option>
            <option value="CRITICAL">Critical Risk</option>
          </select>
        </div>
      </div>

      {/* Action Items List */}
      <div className="relative space-y-0 pt-2">
        <div className="timeline-line" />

        {filteredActions.map((action, idx) => {
          const badge = getStatusBadge(action.decision, action.executionStatus);
          const isPending =
            action.decision === 'REQUIRE_APPROVAL' &&
            action.executionStatus === 'PENDING_APPROVAL';

          return (
            <div
              key={action.actionId || idx}
              className="relative pl-12 pb-5 animate-slide-in cursor-pointer group"
              style={{ animationDelay: `${idx * 0.04}s` }}
              onClick={() => onSelectAction?.(action)}
            >
              {/* Timeline dot */}
              <div className="absolute left-[12px] top-1 z-10">
                {getStatusIcon(action.decision, action.executionStatus)}
              </div>

              {/* Action Card */}
              <div className="bg-[var(--color-bg-primary)] rounded-xl border border-[var(--color-border)] p-4 group-hover:border-cyan-500/40 transition-all duration-200 shadow-sm">
                {/* Top Row: Timestamp + Action Type + Target + Badge */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[0.65rem] font-mono text-[var(--color-text-muted)]">
                      {formatTime(action.timestamp)}
                    </span>
                    <span className="text-[var(--color-text-muted)]">
                      {getActionIcon(action.actionType)}
                    </span>
                    <span className="text-xs font-bold text-[var(--color-text-primary)]">
                      {action.actionType}
                    </span>
                    <span className="text-xs font-mono font-semibold text-cyan-400">
                      {action.target}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`status-badge ${badge.class}`}>
                      {badge.text}
                    </span>
                    <ChevronRight size={14} className="text-[var(--color-text-muted)] group-hover:text-cyan-400 transition-colors" />
                  </div>
                </div>

                {/* Description Intent */}
                {action.description && (
                  <p className="text-xs text-[var(--color-text-secondary)] italic mb-2 line-clamp-2">
                    "{action.description}"
                  </p>
                )}

                {/* Security Flow Pipeline */}
                <div className="flex flex-wrap items-center gap-2 my-2 text-[0.7rem] bg-[var(--color-bg-secondary)] px-3 py-1.5 rounded-lg border border-[var(--color-border)]">
                  <span className="font-mono text-gray-300">
                    {action.agentId
                      ? action.agentId.toLowerCase() === 'antigravity'
                        ? 'Google Antigravity'
                        : action.agentId.toUpperCase()
                      : 'AI Agent'}{' '}
                    → {action.actionType}
                  </span>
                  <span className="text-[var(--color-text-muted)]">|</span>
                  <span className="font-semibold">
                    Gateway: <span className={badge.class.includes('block') || badge.class.includes('rejected') ? 'text-red-400' : badge.class.includes('pending') ? 'text-amber-400' : 'text-emerald-400'}>{badge.text}</span>
                  </span>
                  <span className="text-[var(--color-text-muted)]">|</span>
                  <span className="font-mono">
                    Host: <span className={action.executionStatus === 'EXECUTED' ? 'text-emerald-400' : action.executionStatus === 'PENDING_APPROVAL' ? 'text-amber-400' : 'text-red-400'}>{action.executionStatus}</span>
                  </span>
                </div>

                {/* Telemetry Scores & Classification Pill Bar */}
                <div className="flex flex-wrap items-center gap-3 text-[0.7rem] mt-2">
                  <span className="text-[var(--color-text-muted)]">
                    Alignment:{' '}
                    <span className={`font-bold ${action.goalAlignmentScore >= 80 ? 'text-emerald-400' : action.goalAlignmentScore >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                      {action.goalAlignmentScore ?? action.alignmentScore ?? 100}%
                    </span>
                  </span>
                  <span className="text-[var(--color-text-muted)]">
                    Risk:{' '}
                    <span className={`font-bold ${getRiskColor(action.riskLevel)}`}>
                      {action.riskLevel || 'LOW'}
                    </span>
                  </span>
                  {action.driftScore !== undefined && (
                    <span className="text-[var(--color-text-muted)]">
                      Drift:{' '}
                      <span className={`font-bold ${action.driftScore >= 50 ? 'text-red-400' : 'text-cyan-400'}`}>
                        {action.driftScore}%
                      </span>
                    </span>
                  )}
                  {action.actionClassification && (
                    <span
                      className={`text-[0.6rem] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${
                        action.actionClassification === 'DANGEROUS'
                          ? 'bg-red-500/20 text-red-300 border-red-500/40'
                          : action.actionClassification === 'PRODUCTIVE'
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                          : action.actionClassification === 'RELEVANT'
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                          : 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                      }`}
                    >
                      {action.actionClassification}
                    </span>
                  )}
                </div>

                {/* Why Blocked? Explanation & Button */}
                {(action.decision === 'BLOCK' || action.decision === 'REQUIRE_APPROVAL') && (
                  <div className="mt-2.5 text-xs text-[var(--color-text-muted)] border-t border-[var(--color-border)] pt-2 flex items-center justify-between">
                    <span className="italic truncate max-w-[80%] text-red-300">
                      {action.reason}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectAction?.(action);
                      }}
                      className="text-[0.65rem] font-bold text-red-400 hover:text-red-300 underline shrink-0 ml-2"
                    >
                      Audit Proof Breakdown →
                    </button>
                  </div>
                )}

                {/* HITL Manual Approval Buttons for PENDING_APPROVAL */}
                {isPending && (
                  <div className="flex gap-2 mt-3 pt-3 border-t border-[var(--color-border)]">
                    <button
                      className="btn-approve text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        onApprove?.(action.actionId);
                      }}
                    >
                      APPROVE ACTION
                    </button>
                    <button
                      className="btn-reject text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        onReject?.(action.actionId);
                      }}
                    >
                      REJECT ACTION
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
