import { useState, useEffect, useRef } from 'react';
import { Shield, Radio, CheckCircle2, AlertTriangle, Loader2, Sparkles, X, Terminal, ExternalLink, PowerOff } from 'lucide-react';
import { getAgentStatus, disconnectAgent, connectAgent } from '../services/api';

/**
 * ConnectIdeModal — Accessible modal for pairing Google Antigravity with Agent Guard.
 * Implements actual connection-state flow without fake simulations or VS Code references.
 */
export default function ConnectIdeModal({ isOpen, onClose, initialStatus, onStatusChange }) {
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(initialStatus || null);
  const [confirmDisconnect, setConfirmDisconnect] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    setStatus(initialStatus);
  }, [initialStatus]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const isConnected = Boolean(status?.connected);

  // Real connection trigger: queries real backend Antigravity status & validates hook readiness
  const handleConnect = async () => {
    setConnecting(true);
    setError(null);
    try {
      // 1. Trigger connect / reactivate on backend
      const connectResult = await connectAgent(status?.activeSessionId, status?.activeConversationId);
      setStatus(connectResult);
      if (onStatusChange) onStatusChange(connectResult);

      if (connectResult?.connected) {
        setConnecting(false);
      } else {
        // If not immediately registered, poll for 2.5 seconds to see if Antigravity session handshake completes
        let pollCount = 0;
        const interval = setInterval(async () => {
          pollCount += 1;
          try {
            const check = await getAgentStatus();
            if (check?.connected) {
              clearInterval(interval);
              setStatus(check);
              if (onStatusChange) onStatusChange(check);
              setConnecting(false);
            } else if (pollCount >= 4) {
              clearInterval(interval);
              setConnecting(false);
              setError(
                'No active Antigravity session registered yet. Ensure .agents/hooks.json is enabled in your workspace and trigger any action or prompt in Antigravity.'
              );
            }
          } catch (err) {
            clearInterval(interval);
            setConnecting(false);
            setError(err?.response?.data?.detail || err?.message || 'Agent Guard backend unreachable.');
          }
        }, 600);
      }
    } catch (err) {
      setConnecting(false);
      setError(err?.response?.data?.detail || err?.message || 'Failed to communicate with Agent Guard backend.');
    }
  };

  const handleDisconnect = async () => {
    setDisconnecting(true);
    setError(null);
    try {
      await disconnectAgent(status?.activeSessionId, status?.activeConversationId);
      const updated = await getAgentStatus();
      setStatus(updated);
      if (onStatusChange) onStatusChange(updated);
      setConfirmDisconnect(false);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to disconnect session.');
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

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="connect-ide-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        className="w-full max-w-lg glass-card border border-[var(--color-border)] rounded-2xl p-6 shadow-2xl bg-[var(--color-bg-secondary)] space-y-6 animate-scale-up"
      >
        {/* Modal Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Sparkles size={20} />
            </div>
            <div>
              <h2 id="connect-ide-title" className="text-lg font-bold text-[var(--color-text-primary)]">
                Connect IDE
              </h2>
              <p className="text-xs text-[var(--color-text-secondary)]">
                Connect your AI development environment to Agent Guard.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="text-[var(--color-text-muted)] hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Section: Select Environment */}
        <div className="space-y-3">
          <div className="text-[0.7rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold">
            Select your environment
          </div>

          {/* Google Antigravity Card */}
          <div
            className={`p-4 rounded-xl border transition-all duration-200 ${
              isConnected
                ? 'bg-emerald-950/20 border-emerald-500/40'
                : 'bg-[var(--color-bg-primary)]/70 border-cyan-500/30 hover:border-cyan-500/60'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mt-0.5">
                  <Radio size={18} className={isConnected ? 'text-emerald-400' : 'text-cyan-400'} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-[var(--color-text-primary)]">
                      ✦ Google Antigravity
                    </span>
                    <span
                      className={`text-[0.65rem] font-bold px-2 py-0.5 rounded-full border ${
                        isConnected
                          ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                          : 'text-gray-400 bg-gray-500/10 border-gray-500/30'
                      }`}
                    >
                      {isConnected ? '● CONNECTED' : '○ NOT CONNECTED'}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                    AI-powered development runtime with PreInvocation & PreToolUse security hooks.
                  </p>
                </div>
              </div>
            </div>

            {/* Live Session Telemetry when Connected */}
            {isConnected && (
              <div className="mt-3 pt-3 border-t border-[var(--color-border)] grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[0.65rem] text-[var(--color-text-muted)] block">Active Session</span>
                  <span className="font-mono text-cyan-400 font-semibold">
                    {status?.activeSessionId ? `S-${status.activeSessionId.slice(0, 8)}` : 'S-ACTIVE'}
                  </span>
                </div>
                <div>
                  <span className="text-[0.65rem] text-[var(--color-text-muted)] block">Last Activity</span>
                  <span className="text-[var(--color-text-secondary)] font-medium">
                    {formatLastSeen(status?.lastSeenAt)}
                  </span>
                </div>
                {status?.userGoal && (
                  <div className="col-span-2 mt-1">
                    <span className="text-[0.65rem] text-[var(--color-text-muted)] block">Active Goal</span>
                    <span className="text-xs text-[var(--color-text-primary)] line-clamp-1">
                      {status.userGoal}
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Actions Inside Card */}
            <div className="mt-4 flex items-center justify-between gap-3">
              <span className="text-[0.65rem] text-[var(--color-text-muted)] flex items-center gap-1">
                <Terminal size={11} />
                Protocol: Native Agent Hook Bridge
              </span>

              {isConnected ? (
                confirmDisconnect ? (
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
                      Confirm Disconnect
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmDisconnect(true)}
                    className="px-3 py-1.5 text-xs rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors font-medium"
                  >
                    Disconnect
                  </button>
                )
              ) : (
                <button
                  onClick={handleConnect}
                  disabled={connecting}
                  className="btn-primary text-xs px-4 py-1.5 flex items-center gap-1.5 shadow-md shadow-cyan-500/20"
                  style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
                >
                  {connecting ? (
                    <>
                      <Loader2 size={13} className="animate-spin" />
                      Connecting...
                    </>
                  ) : (
                    <>
                      <Radio size={13} />
                      CONNECT
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Connection Error Banner */}
          {error && (
            <div className="p-3 rounded-xl bg-red-950/30 border border-red-500/30 text-red-300 text-xs space-y-2 animate-fade-in">
              <div className="flex items-center gap-2 font-semibold text-red-400">
                <AlertTriangle size={15} />
                ⚠ Unable to connect to Antigravity
              </div>
              <div className="text-[0.7rem] text-red-200/80 leading-relaxed">
                Reason: {error}
              </div>
              <button
                onClick={handleConnect}
                disabled={connecting}
                className="px-3 py-1 rounded bg-red-500/20 hover:bg-red-500/30 text-red-300 text-[0.7rem] font-semibold transition-colors"
              >
                RETRY
              </button>
            </div>
          )}

          {/* More Integrations Notice */}
          <div className="text-center py-2">
            <span className="text-[0.7rem] text-[var(--color-text-muted)] italic">
              More integrations coming soon
            </span>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="pt-3 border-t border-[var(--color-border)] flex items-center justify-between">
          <div className="flex items-center gap-1 text-[0.65rem] text-[var(--color-text-muted)]">
            <Shield size={11} className="text-cyan-400" />
            Agent Guard protects the actions of your connected AI agent.
          </div>
          <button
            onClick={onClose}
            className="btn-secondary px-4 py-1.5 text-xs text-[var(--color-text-muted)] hover:text-white"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
