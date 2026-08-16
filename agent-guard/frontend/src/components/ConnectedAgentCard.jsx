import { useState } from 'react';
import { Radio, Plus, PowerOff, FileCode, ArrowRight, Loader2, FolderRoot } from 'lucide-react';
import { disconnectAgent } from '../services/api';

/**
 * ConnectedAgentCard — Displays real-time connected agent status on the Home page & Dashboard.
 * Supports NOT CONNECTED, CONNECTING, CONNECTED, and DISCONNECT flow with live backend data.
 */
export default function ConnectedAgentCard({ status, onOpenConnectModal, onViewActivity, onStatusChange }) {
  const [confirmDisconnect, setConfirmDisconnect] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  const isConnected = Boolean(status?.connected);

  const handleDisconnect = async () => {
    setDisconnecting(true);
    try {
      await disconnectAgent(status?.activeSessionId, status?.activeConversationId);
      if (onStatusChange) {
        onStatusChange({
          ...status,
          connected: false,
          status: 'NOT_CONNECTED',
          activeSessionId: null,
          activeGoalId: null,
        });
      }
      setConfirmDisconnect(false);
    } catch (err) {
      console.error('Failed to disconnect agent:', err);
    } finally {
      setDisconnecting(false);
    }
  };

  // Format relative last seen
  const formatLastSeen = (isoStr) => {
    if (!isoStr) return 'Never';
    const diff = Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000);
    if (diff < 5) return 'Just now';
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  };

  // If Not Connected, show clean Quick Status banner with prominent [+ CONNECT IDE] button
  if (!isConnected) {
    return (
      <div className="glass-card p-4 border border-[var(--color-border)] rounded-xl bg-[var(--color-bg-secondary)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
        <div className="flex items-start sm:items-center gap-3 min-w-0">
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gray-500/10 border border-gray-500/20 flex items-center justify-center text-gray-400 shrink-0">
            <Radio size={18} />
          </div>
          <div className="min-w-0">
            <div className="text-[0.6rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-[var(--color-text-muted)] flex items-center gap-1.5">
              AGENT CONNECTION
            </div>
            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
              <span className="text-xs sm:text-sm font-bold text-[var(--color-text-primary)] flex items-center gap-1.5 truncate">
                ✦ Antigravity
              </span>
              <span className="text-[0.6rem] sm:text-[0.65rem] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border text-gray-400 bg-gray-500/10 border-gray-500/30 shrink-0">
                ○ NOT CONNECTED
              </span>
            </div>
            <div className="text-[0.65rem] sm:text-[0.7rem] text-[var(--color-text-muted)] mt-0.5 leading-relaxed">
              Connect your AI development environment to enable real-time goal integrity & action authorization.
            </div>
          </div>
        </div>

        <button
          onClick={onOpenConnectModal}
          className="btn-primary text-xs px-3.5 sm:px-4 py-2 flex items-center gap-1.5 font-bold tracking-wide shadow-md shadow-cyan-500/20 whitespace-nowrap self-start sm:self-auto shrink-0"
          style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
        >
          <Plus size={14} />
          CONNECT IDE
        </button>
      </div>
    );
  }

  // Connected State: Full Compact Card with real backend data
  const lastAction = status?.lastAction;
  const interceptedCount = status?.interceptedCount ?? 0;
  const allowedCount = status?.allowedCount ?? 0;
  const blockedCount = status?.blockedCount ?? 0;
  const approvalCount = status?.approvalCount ?? 0;

  return (
    <div className="glass-card p-4 sm:p-5 border border-cyan-500/30 bg-[var(--color-bg-secondary)] rounded-xl space-y-3.5 sm:space-y-4 shadow-lg shadow-cyan-500/5 animate-fade-in min-w-0">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
          <span className="text-xs font-extrabold tracking-wider text-cyan-400 flex items-center gap-1.5">
            ✦ GOOGLE ANTIGRAVITY
          </span>
          <span className="text-[0.6rem] sm:text-[0.65rem] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border text-emerald-400 bg-emerald-500/10 border-emerald-500/30 flex items-center gap-1 shrink-0">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            CONNECTED
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[0.65rem] sm:text-[0.7rem] text-[var(--color-text-muted)]">
            Last Activity: <strong className="text-[var(--color-text-secondary)]">{formatLastSeen(status?.lastSeenAt)}</strong>
          </span>
        </div>
      </div>

      {/* Main Metadata Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 sm:gap-3 text-xs">
        {/* Session & Workspace */}
        <div className="p-2.5 sm:p-3 rounded-lg bg-[var(--color-bg-primary)]/60 border border-[var(--color-border)] space-y-1 min-w-0">
          <div className="flex items-center justify-between text-[0.65rem] sm:text-[0.7rem]">
            <span className="text-[var(--color-text-muted)]">Session:</span>
            <span className="font-mono text-cyan-400 font-bold truncate">
              {status?.activeSessionId ? `S-${status.activeSessionId.slice(0, 8)}` : 'S-ACTIVE'}
            </span>
          </div>
          {status?.workspace && (
            <div className="flex items-center justify-between text-[0.65rem] sm:text-[0.7rem] pt-1 border-t border-[var(--color-border)]">
              <span className="text-[var(--color-text-muted)] flex items-center gap-1">
                <FolderRoot size={11} /> Workspace:
              </span>
              <span className="font-mono text-[var(--color-text-secondary)] truncate max-w-[150px]" title={status.workspace}>
                {status.workspace.split(/[/\\]/).pop() || status.workspace}
              </span>
            </div>
          )}
        </div>

        {/* Current Goal */}
        <div className="p-2.5 sm:p-3 rounded-lg bg-[var(--color-bg-primary)]/60 border border-[var(--color-border)] space-y-1 min-w-0">
          <div className="text-[0.6rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
            Current Goal
          </div>
          <div className="text-[0.7rem] sm:text-xs text-[var(--color-text-primary)] font-medium line-clamp-2 leading-normal">
            {status?.userGoal || 'Autonomous development task in progress'}
          </div>
        </div>
      </div>

      {/* Last Action Intercepted */}
      {lastAction && (
        <div className="p-2 sm:p-2.5 rounded-lg bg-cyan-950/20 border border-cyan-500/20 flex flex-wrap sm:flex-nowrap items-center justify-between gap-2 text-xs min-w-0">
          <div className="flex items-center gap-2 overflow-hidden min-w-0">
            <FileCode size={13} className="text-cyan-400 flex-shrink-0" />
            <div className="truncate min-w-0">
              <span className="font-mono text-cyan-300 font-bold text-[0.65rem] sm:text-[0.7rem] uppercase mr-1">
                {lastAction.actionType || 'TOOL_CALL'} →
              </span>
              <span className="text-[var(--color-text-secondary)] font-mono text-[0.7rem] sm:text-[0.75rem] break-all">
                {lastAction.target || lastAction.description || 'file operation'}
              </span>
            </div>
          </div>
          <span
            className={`text-[0.6rem] sm:text-[0.65rem] font-bold uppercase px-2 py-0.5 rounded border flex-shrink-0 self-start sm:self-auto ${
              lastAction.decision === 'DENY' || lastAction.decision === 'BLOCK'
                ? 'text-red-400 bg-red-500/10 border-red-500/30'
                : lastAction.decision === 'REQUIRE_APPROVAL' || lastAction.decision === 'ASK'
                ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
                : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
            }`}
          >
            {lastAction.decision || 'ALLOW'}
          </span>
        </div>
      )}

      {/* Telemetry Summary Counters */}
      <div className="grid grid-cols-4 gap-1.5 sm:gap-2 pt-1">
        <div className="p-1.5 sm:p-2 rounded-lg bg-[var(--color-bg-primary)]/40 border border-[var(--color-border)] text-center">
          <div className="text-[0.55rem] sm:text-[0.65rem] text-[var(--color-text-muted)] uppercase truncate">Intercept</div>
          <div className="text-xs sm:text-sm font-bold font-mono text-cyan-400">{interceptedCount}</div>
        </div>
        <div className="p-1.5 sm:p-2 rounded-lg bg-[var(--color-bg-primary)]/40 border border-[var(--color-border)] text-center">
          <div className="text-[0.55rem] sm:text-[0.65rem] text-emerald-400 uppercase truncate">Allowed</div>
          <div className="text-xs sm:text-sm font-bold font-mono text-emerald-400">{allowedCount}</div>
        </div>
        <div className="p-1.5 sm:p-2 rounded-lg bg-[var(--color-bg-primary)]/40 border border-[var(--color-border)] text-center">
          <div className="text-[0.55rem] sm:text-[0.65rem] text-red-400 uppercase truncate">Blocked</div>
          <div className="text-xs sm:text-sm font-bold font-mono text-red-400">{blockedCount}</div>
        </div>
        <div className="p-1.5 sm:p-2 rounded-lg bg-[var(--color-bg-primary)]/40 border border-[var(--color-border)] text-center">
          <div className="text-[0.55rem] sm:text-[0.65rem] text-amber-400 uppercase truncate">Approval</div>
          <div className="text-xs sm:text-sm font-bold font-mono text-amber-400">{approvalCount}</div>
        </div>
      </div>

      {/* Card Actions: View Activity & Disconnect */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-[var(--color-border)]">
        {onViewActivity ? (
          <button
            onClick={onViewActivity}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1 transition-colors"
          >
            VIEW ACTIVITY
            <ArrowRight size={12} />
          </button>
        ) : (
          <span className="text-[0.65rem] text-[var(--color-text-muted)]">
            Agent Guard Gateway
          </span>
        )}

        {confirmDisconnect ? (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setConfirmDisconnect(false)}
              disabled={disconnecting}
              className="px-2.5 py-1 text-xs rounded border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleDisconnect}
              disabled={disconnecting}
              className="px-3 py-1 text-xs rounded bg-red-600/20 text-red-400 border border-red-500/30 hover:bg-red-600 hover:text-white transition-colors font-medium flex items-center gap-1"
            >
              {disconnecting ? <Loader2 size={12} className="animate-spin" /> : <PowerOff size={12} />}
              Confirm
            </button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmDisconnect(true)}
            className="px-2.5 sm:px-3 py-1 text-xs rounded border border-red-500/20 text-red-400 hover:bg-red-500/10 transition-colors font-medium"
          >
            DISCONNECT
          </button>
        )}
      </div>
    </div>
  );
}
