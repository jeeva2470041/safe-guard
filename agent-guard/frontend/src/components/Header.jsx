import { Shield } from 'lucide-react';

/**
 * Header — AGENT GUARD branding with agent status indicator.
 */
export default function Header({ agentStatus = 'IDLE', onReset }) {
  const statusConfig = {
    IDLE: { color: 'bg-gray-500', text: 'IDLE', pulse: false },
    ACTIVE: { color: 'bg-blue-500', text: 'AGENT READY', pulse: false },
    RUNNING: { color: 'bg-emerald-500', text: '● AGENT RUNNING', pulse: true },
    WARNING: { color: 'bg-amber-500', text: '⚠ AGENT AT RISK', pulse: true },
    PAUSED: { color: 'bg-red-500', text: '⏸ AGENT PAUSED', pulse: true },
    WAITING_FOR_APPROVAL: { color: 'bg-amber-500', text: 'WAITING FOR APPROVAL', pulse: true },
    BLOCKED_ACTION: { color: 'bg-red-500', text: 'ACTION BLOCKED', pulse: false },
    COMPLETED: { color: 'bg-cyan-500', text: 'GOAL COMPLETED', pulse: false },
    FAILED: { color: 'bg-red-600', text: 'AGENT FAILED', pulse: false },
    STOPPED: { color: 'bg-gray-600', text: 'AGENT STOPPED', pulse: false },
  };

  const status = statusConfig[agentStatus] || statusConfig.IDLE;

  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)]/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-[1440px] mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Shield size={22} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-[var(--color-text-primary)]">
              AGENT GUARD
            </h1>
            <p className="text-[0.7rem] text-[var(--color-text-muted)] tracking-wide uppercase">
              Runtime Goal Integrity & Action Authorization
            </p>
          </div>
        </div>

        {/* Agent Status + Reset */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 rounded-full border border-[var(--color-border)] bg-[var(--color-bg-primary)]">
            <span
              className={`w-2.5 h-2.5 rounded-full ${status.color} ${
                status.pulse ? 'animate-status-dot' : ''
              }`}
            />
            <span className="text-xs font-semibold tracking-wider text-[var(--color-text-secondary)]">
              {status.text}
            </span>
          </div>

          {onReset && (
            <button onClick={onReset} className="btn-reset">
              RESET DEMO
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
