import { Shield, Plus, Radio } from 'lucide-react';
import GuardModeToggle from './GuardModeToggle';

/**
 * Header — AGENT GUARD branding with agent status indicator, Guard Mode Toggle, and Connect IDE button.
 */
export default function Header({ agentStatus = 'IDLE', onReset, sessionStatus, onOpenConnectModal, onGuardModeChange }) {
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
  const isAgentConnected = Boolean(sessionStatus?.connected);

  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)]/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-[1440px] mx-auto px-6 py-4 flex flex-wrap items-center justify-between gap-4">
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

        {/* Right Section: Mode Toggle + Connected Agent Badge + Connect IDE button + System Status + Reset */}
        <div className="flex items-center gap-3">
          {/* Interactive Guard Mode Toggle */}
          <GuardModeToggle onChange={onGuardModeChange} />
          {/* Connected Agent Quick Badge */}
          <div
            onClick={onOpenConnectModal}
            className={`cursor-pointer hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full border transition-colors ${
              isAgentConnected
                ? 'bg-emerald-950/20 border-emerald-500/30 hover:border-emerald-500/50 text-emerald-400'
                : 'bg-[var(--color-bg-primary)] border-[var(--color-border)] hover:border-cyan-500/40 text-[var(--color-text-secondary)]'
            }`}
            title="Click to manage AI IDE connections"
          >
            <Radio size={13} className={isAgentConnected ? 'animate-pulse' : 'text-gray-400'} />
            <span className="text-xs font-semibold">
              {isAgentConnected ? 'Antigravity Connected' : 'Antigravity Disconnected'}
            </span>
            <span
              className={`w-2 h-2 rounded-full ${
                isAgentConnected ? 'bg-emerald-400 animate-ping' : 'bg-gray-500'
              }`}
            />
          </div>

          {/* Connect IDE Button */}
          {onOpenConnectModal && (
            <button
              onClick={onOpenConnectModal}
              className="btn-primary text-xs px-3.5 py-1.5 flex items-center gap-1.5 font-bold shadow-md shadow-cyan-500/20"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
            >
              <Plus size={14} />
              <span>CONNECT IDE</span>
            </button>
          )}

          {/* Execution State */}
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-[var(--color-border)] bg-[var(--color-bg-primary)]">
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

