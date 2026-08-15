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
} from 'lucide-react';

/**
 * ActivityTimeline — Live vertical timeline of agent actions
 * with status badges, alignment scores, and approval buttons.
 */
export default function ActivityTimeline({
  actions = [],
  onApprove,
  onReject,
  onSelectAction,
}) {
  const getStatusIcon = (decision, executionStatus) => {
    if (decision === 'ALLOW' || decision === 'APPROVED' || executionStatus === 'EXECUTED') {
      return <CheckCircle2 size={18} className="text-emerald-400" />;
    }
    if (decision === 'REQUIRE_APPROVAL' && executionStatus === 'PENDING_APPROVAL') {
      return <AlertTriangle size={18} className="text-amber-400" />;
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
    if (type === 'ACCESS_FILE') return <Key size={14} />;
    if (type === 'MODIFY_FILE') return <Edit size={14} />;
    if (type === 'RUN_TESTS') return <Play size={14} />;
    if (type === 'RUN_COMMAND') return <Terminal size={14} />;
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

  const safeActions = Array.isArray(actions) ? actions : [];

  if (safeActions.length === 0) {
    return (
      <div className="glass-card p-6 text-center animate-fade-in-up">
        <Clock size={32} className="text-[var(--color-text-muted)] mx-auto mb-3" />
        <p className="text-sm text-[var(--color-text-muted)]">
          Waiting for agent to start...
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card p-5 animate-fade-in-up">
      <div className="flex items-center gap-2 mb-4">
        <Activity size={16} className="text-cyan-400" />
        <span className="text-xs font-semibold tracking-wider uppercase text-[var(--color-text-muted)]">
          Live Agent Activity
        </span>
        <span className="ml-auto text-[0.65rem] font-mono text-[var(--color-text-muted)]">
          {safeActions.length} actions
        </span>
      </div>

      <div className="relative space-y-0">
        {/* Timeline vertical line */}
        <div className="timeline-line" />

        {safeActions.map((action, idx) => {
          const badge = getStatusBadge(action.decision, action.executionStatus);
          const isPending =
            action.decision === 'REQUIRE_APPROVAL' &&
            action.executionStatus === 'PENDING_APPROVAL';

          return (
            <div
              key={action.actionId}
              className="relative pl-12 pb-5 animate-slide-in cursor-pointer group"
              style={{ animationDelay: `${idx * 0.05}s` }}
              onClick={() => onSelectAction?.(action)}
            >
              {/* Timeline dot */}
              <div className="absolute left-[12px] top-1 z-10">
                {getStatusIcon(action.decision, action.executionStatus)}
              </div>

              {/* Card */}
              <div className="bg-[var(--color-bg-primary)] rounded-lg border border-[var(--color-border)] p-4 group-hover:border-[var(--color-border-light)] transition-colors">
                {/* Timestamp */}
                <div className="text-[0.65rem] font-mono text-[var(--color-text-muted)] mb-2">
                  {formatTime(action.timestamp)}
                </div>

                {/* Action type + target */}
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[var(--color-text-muted)]">
                    {getActionIcon(action.actionType)}
                  </span>
                  <span className="text-sm font-semibold text-[var(--color-text-primary)]">
                    {action.actionType}
                  </span>
                  <span className="text-sm font-mono text-[var(--color-accent-cyan)]">
                    {action.target}
                  </span>
                </div>

                {/* Flow Breakdown */}
                <div className="flex flex-wrap items-center gap-2 my-2 text-xs">
                  <span className="font-mono text-gray-300">{action.agentId ? (action.agentId.toLowerCase() === 'antigravity' ? 'Google Antigravity' : action.agentId.toUpperCase()) : 'OpenAI Agent'} → {action.actionType} {action.target}</span>
                  <span className="text-[var(--color-text-muted)]">|</span>
                  <span className="font-semibold">Security Gateway → <span className={badge.class.includes('block') || badge.class.includes('rejected') ? 'text-red-400' : badge.class.includes('pending') ? 'text-amber-400' : 'text-emerald-400'}>{badge.text}</span></span>
                  <span className="text-[var(--color-text-muted)]">|</span>
                  <span className="font-mono">Tool → <span className={action.executionStatus === 'EXECUTED' ? 'text-emerald-400' : action.executionStatus === 'PENDING_APPROVAL' ? 'text-amber-400' : 'text-red-400'}>{action.executionStatus}</span></span>
                </div>

                {/* Status badge & Scores & Classification */}
                <div className="flex flex-wrap items-center gap-3 text-[0.7rem] mt-2">
                  <span className="text-[var(--color-text-muted)]">
                    Alignment:{' '}
                    <span className={`font-semibold ${action.goalAlignmentScore >= 80 ? 'text-emerald-400' : action.goalAlignmentScore >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                      {action.goalAlignmentScore ?? action.alignmentScore ?? 100}%
                    </span>
                  </span>
                  <span className="text-[var(--color-text-muted)]">
                    Risk:{' '}
                    <span className={`font-semibold ${getRiskColor(action.riskLevel)}`}>
                      {action.riskLevel}
                    </span>
                  </span>
                  {action.driftScore !== undefined && (
                    <span className="text-[var(--color-text-muted)]">
                      Drift:{' '}
                      <span className={`font-semibold ${action.driftScore >= 50 ? 'text-red-400' : 'text-cyan-400'}`}>
                        {action.driftScore}%
                      </span>
                    </span>
                  )}
                  {action.actionClassification && (
                    <span className={`text-[0.6rem] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${
                      action.actionClassification === 'DANGEROUS'
                        ? 'bg-red-500/20 text-red-300 border-red-500/40'
                        : action.actionClassification === 'PRODUCTIVE'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : action.actionClassification === 'RELEVANT'
                        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                        : 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                    }`}>
                      {action.actionClassification}
                    </span>
                  )}
                </div>

                {/* Verification Layer Result */}
                {action.verificationMessage && (
                  <div className="mt-2.5 px-3 py-1.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-[0.7rem] font-mono text-cyan-300 flex items-center justify-between">
                    <span>{action.verificationMessage}</span>
                    <span className="text-[0.65rem] font-bold px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-200">
                      {action.verificationStatus || 'PASSED'}
                    </span>
                  </div>
                )}

                {/* Reason & Policy Explanation for blocked or pending actions */}
                {(action.decision === 'BLOCK' || action.decision === 'REQUIRE_APPROVAL') && (
                  <div className="mt-2 text-[0.7rem] text-[var(--color-text-muted)] border-t border-[var(--color-border)] pt-2 flex items-center justify-between">
                    <span className="italic truncate max-w-[80%]">{action.reason}</span>
                    {action.decision === 'BLOCK' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectAction?.(action);
                        }}
                        className="text-[0.65rem] font-bold text-red-400 hover:text-red-300 underline shrink-0 ml-2"
                      >
                        Why Blocked?
                      </button>
                    )}
                  </div>
                )}

                {/* Approval buttons */}
                {isPending && (
                  <div className="flex gap-2 mt-3 pt-3 border-t border-[var(--color-border)]">
                    <button
                      className="btn-approve"
                      onClick={(e) => {
                        e.stopPropagation();
                        onApprove?.(action.actionId);
                      }}
                    >
                      APPROVE
                    </button>
                    <button
                      className="btn-reject"
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
