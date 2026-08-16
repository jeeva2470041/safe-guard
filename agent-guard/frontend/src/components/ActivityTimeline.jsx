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
  ChevronRight,
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
      return <CheckCircle2 size={16} className="text-emerald-400" />;
    }
    if (decision === 'REQUIRE_APPROVAL' && executionStatus === 'PENDING_APPROVAL') {
      return <AlertTriangle size={16} className="text-amber-400 animate-pulse" />;
    }
    if (decision === 'BLOCK' || decision === 'REJECTED' || executionStatus === 'NOT_EXECUTED') {
      return <XCircle size={16} className="text-red-400" />;
    }
    return <Clock size={16} className="text-gray-400" />;
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
    if (type === 'DELETE_FILE') return <Trash2 size={13} />;
    if (type === 'ACCESS_SECRET' || type === 'ACCESS_FILE' || type === 'ACCESS_ENV') return <Key size={13} />;
    if (type === 'MODIFY_FILE' || type === 'FILE_WRITE') return <Edit size={13} />;
    if (type === 'RUN_TESTS') return <Play size={13} />;
    if (type === 'RUN_COMMAND' || type === 'COMMAND_EXECUTION') return <Terminal size={13} />;
    return <FileText size={13} />;
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
      <div className="glass-card p-6 sm:p-8 text-center animate-fade-in-up space-y-3">
        <Clock size={32} className="text-[var(--color-text-muted)] mx-auto opacity-70" />
        <h4 className="text-xs sm:text-sm font-bold text-[var(--color-text-primary)]">
          Awaiting Agent Actions
        </h4>
        <p className="text-[0.7rem] sm:text-xs text-[var(--color-text-muted)] max-w-sm mx-auto">
          Start a scenario or trigger an action in Antigravity to stream real-time PreToolUse security evaluations.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card p-3.5 sm:p-5 animate-fade-in-up space-y-4">
      {/* Header & Stats Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-3 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2 flex-wrap">
          <Activity size={15} className="text-cyan-400 shrink-0" />
          <span className="text-xs font-bold tracking-wider uppercase text-[var(--color-text-primary)]">
            Live Interception Stream
          </span>
          <span className="text-[0.6rem] sm:text-[0.65rem] font-mono px-2 py-0.5 rounded bg-[var(--color-bg-primary)] border border-[var(--color-border)] text-cyan-300">
            {filteredActions.length} / {stats.total} actions
          </span>
        </div>

        {/* Quick Stats Pills */}
        <div className="flex items-center gap-1.5 sm:gap-2 text-[0.6rem] sm:text-[0.65rem] font-mono flex-wrap">
          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
            ✓ {stats.allowed}
          </span>
          <span className="px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-bold">
            ✕ {stats.blocked}
          </span>
          {stats.pending > 0 && (
            <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 font-bold animate-pulse">
              ⏳ {stats.pending} Approval
            </span>
          )}
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-2.5">
        {/* Search Input */}
        <div className="sm:col-span-6 relative">
          <Search size={13} className="absolute left-2.5 top-2.5 text-[var(--color-text-muted)]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search target path, tool, command..."
            className="w-full pl-8 pr-3 py-1.5 bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg text-xs text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-cyan-500 font-sans"
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

        {/* Verdict Filter Chips & Risk Level */}
        <div className="sm:col-span-6 flex items-center gap-1.5 flex-wrap justify-between sm:justify-start">
          <div className="flex items-center gap-1 flex-wrap">
            {['ALL', 'ALLOW', 'BLOCK', 'PENDING'].map((v) => (
              <button
                key={v}
                onClick={() => setVerdictFilter(v)}
                className={`text-[0.6rem] sm:text-[0.65rem] px-2 py-1 rounded-md font-semibold transition-all ${
                  verdictFilter === v
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'bg-[var(--color-bg-primary)] text-[var(--color-text-muted)] border border-[var(--color-border)] hover:text-white'
                }`}
              >
                {v}
              </button>
            ))}
          </div>

          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="text-[0.6rem] sm:text-[0.65rem] px-2 py-1 bg-[var(--color-bg-primary)] text-[var(--color-text-secondary)] border border-[var(--color-border)] rounded-md focus:outline-none ml-auto"
          >
            <option value="ALL">All Risk</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Med</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Crit</option>
          </select>
        </div>
      </div>

      {/* Action Items List */}
      <div className="relative space-y-0 pt-2">
        <div className="timeline-line left-[14px] sm:left-[20px]" />

        {filteredActions.map((action, idx) => {
          const badge = getStatusBadge(action.decision, action.executionStatus);
          const isPending =
            action.decision === 'REQUIRE_APPROVAL' &&
            action.executionStatus === 'PENDING_APPROVAL';

          return (
            <div
              key={action.actionId || idx}
              className="relative pl-8 sm:pl-12 pb-4 animate-slide-in cursor-pointer group"
              style={{ animationDelay: `${idx * 0.03}s` }}
              onClick={() => onSelectAction?.(action)}
            >
              {/* Timeline dot */}
              <div className="absolute left-[7px] sm:left-[12px] top-1.5 z-10 bg-[var(--color-bg-card)] rounded-full">
                {getStatusIcon(action.decision, action.executionStatus)}
              </div>

              {/* Action Card */}
              <div className="bg-[var(--color-bg-primary)] rounded-xl border border-[var(--color-border)] p-3 sm:p-4 group-hover:border-cyan-500/40 transition-all duration-200 shadow-sm min-w-0">
                {/* Top Row: Timestamp + Action Type + Target + Badge */}
                <div className="flex flex-wrap items-center justify-between gap-1.5 mb-1.5">
                  <div className="flex items-center gap-1.5 sm:gap-2 min-w-0 flex-wrap">
                    <span className="text-[0.6rem] sm:text-[0.65rem] font-mono text-[var(--color-text-muted)] shrink-0">
                      {formatTime(action.timestamp)}
                    </span>
                    <span className="text-[var(--color-text-muted)] shrink-0">
                      {getActionIcon(action.actionType)}
                    </span>
                    <span className="text-xs font-bold text-[var(--color-text-primary)] shrink-0">
                      {action.actionType}
                    </span>
                    <span className="text-xs font-mono font-semibold text-cyan-400 break-all">
                      {action.target}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0 ml-auto">
                    <span className={`status-badge text-[0.65rem] px-2 py-0.5 ${badge.class}`}>
                      {badge.text}
                    </span>
                    <ChevronRight size={13} className="text-[var(--color-text-muted)] group-hover:text-cyan-400 transition-colors shrink-0" />
                  </div>
                </div>

                {/* Description Intent */}
                {action.description && (
                  <p className="text-[0.7rem] sm:text-xs text-[var(--color-text-secondary)] italic mb-2 break-words leading-relaxed">
                    "{action.description}"
                  </p>
                )}

                {/* Security Flow Pipeline */}
                <div className="flex flex-wrap items-center gap-1 sm:gap-2 my-2 text-[0.65rem] sm:text-[0.7rem] bg-[var(--color-bg-secondary)] p-2 sm:px-3 sm:py-1.5 rounded-lg border border-[var(--color-border)] break-words leading-normal">
                  <span className="font-mono text-gray-300 truncate">
                    {action.agentId
                      ? action.agentId.toLowerCase() === 'antigravity'
                        ? 'Google Antigravity'
                        : action.agentId.toUpperCase()
                      : 'AI Agent'}{' '}
                    → {action.actionType}
                  </span>
                  <span className="text-[var(--color-text-muted)]">|</span>
                  <span className="font-semibold">
                    Gateway:{' '}
                    <span className={badge.class.includes('block') || badge.class.includes('rejected') ? 'text-red-400' : badge.class.includes('pending') ? 'text-amber-400' : 'text-emerald-400'}>
                      {badge.text}
                    </span>
                  </span>
                  <span className="text-[var(--color-text-muted)]">|</span>
                  <span className="font-mono">
                    Host:{' '}
                    <span className={action.executionStatus === 'EXECUTED' ? 'text-emerald-400' : action.executionStatus === 'PENDING_APPROVAL' ? 'text-amber-400' : 'text-red-400'}>
                      {action.executionStatus}
                    </span>
                  </span>
                </div>

                {/* Telemetry Scores & Classification Pill Bar */}
                <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-[0.65rem] sm:text-[0.7rem] mt-2">
                  <span className="text-[var(--color-text-muted)]">
                    Align:{' '}
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
                      className={`text-[0.55rem] sm:text-[0.6rem] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${
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
                  <div className="mt-2.5 text-[0.7rem] sm:text-xs text-[var(--color-text-muted)] border-t border-[var(--color-border)] pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
                    <span className="italic text-red-300 break-words">
                      {action.reason}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectAction?.(action);
                      }}
                      className="text-[0.65rem] font-bold text-red-400 hover:text-red-300 underline shrink-0 self-start sm:self-auto"
                    >
                      Audit Proof Breakdown →
                    </button>
                  </div>
                )}

                {/* HITL Manual Approval Buttons for PENDING_APPROVAL */}
                {isPending && (
                  <div className="flex gap-2 mt-3 pt-3 border-t border-[var(--color-border)]">
                    <button
                      className="btn-approve text-xs py-1.5 px-3 flex-1 sm:flex-initial"
                      onClick={(e) => {
                        e.stopPropagation();
                        onApprove?.(action.actionId);
                      }}
                    >
                      APPROVE
                    </button>
                    <button
                      className="btn-reject text-xs py-1.5 px-3 flex-1 sm:flex-initial"
                      onClick={(e) => {
                        e.stopPropagation();
                        onReject?.(action.actionId);
                      }}
                    >
                      REJECT
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
