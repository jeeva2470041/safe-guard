import { Shield, Plus, Radio, Sparkles } from 'lucide-react';
import ThemeToggle from './ThemeToggle';

/**
 * Header — Premium AGENT GUARD branding with live agent status, Theme Toggle, and Connect IDE controls.
 */
export default function Header({ agentStatus = 'IDLE', onReset, sessionStatus, onOpenConnectModal }) {
  const statusConfig = {
    IDLE: { color: 'bg-gray-500', text: 'IDLE', pulse: false, border: 'border-gray-500/30', bg: 'bg-gray-500/10' },
    ACTIVE: { color: 'bg-blue-500', text: 'AGENT READY', pulse: false, border: 'border-blue-500/30', bg: 'bg-blue-500/10' },
    RUNNING: { color: 'bg-emerald-500', text: 'AGENT RUNNING', pulse: true, border: 'border-emerald-500/30', bg: 'bg-emerald-500/10' },
    WARNING: { color: 'bg-amber-500', text: 'AGENT AT RISK', pulse: true, border: 'border-amber-500/30', bg: 'bg-amber-500/10' },
    PAUSED: { color: 'bg-red-500', text: 'AGENT PAUSED', pulse: true, border: 'border-red-500/30', bg: 'bg-red-500/10' },
    WAITING_FOR_APPROVAL: { color: 'bg-amber-500', text: 'WAITING FOR APPROVAL', pulse: true, border: 'border-amber-500/30', bg: 'bg-amber-500/10' },
    BLOCKED_ACTION: { color: 'bg-red-500', text: 'ACTION BLOCKED', pulse: false, border: 'border-red-500/30', bg: 'bg-red-500/10' },
    COMPLETED: { color: 'bg-cyan-500', text: 'GOAL COMPLETED', pulse: false, border: 'border-cyan-500/30', bg: 'bg-cyan-500/10' },
    FAILED: { color: 'bg-red-600', text: 'AGENT FAILED', pulse: false, border: 'border-red-600/30', bg: 'bg-red-600/10' },
    STOPPED: { color: 'bg-gray-600', text: 'AGENT STOPPED', pulse: false, border: 'border-gray-600/30', bg: 'bg-gray-600/10' },
  };

  const status = statusConfig[agentStatus] || statusConfig.IDLE;
  const isAgentConnected = Boolean(sessionStatus?.connected);

  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)]/90 backdrop-blur-xl sticky top-0 z-40 transition-colors duration-200 shadow-sm">
      <div className="max-w-[1440px] mx-auto px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        {/* Logo & Title */}
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/25 ring-1 ring-white/20">
            <Shield size={22} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold tracking-tight text-[var(--color-text-primary)]">
                AGENT GUARD
              </h1>
              <span className="text-[0.6rem] font-extrabold uppercase px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 tracking-wider">
                SOC v5.0
              </span>
            </div>
            <p className="text-[0.7rem] text-[var(--color-text-muted)] tracking-wide font-medium">
              Runtime Goal Integrity & Action Authorization
            </p>
          </div>
        </div>

        {/* Right Section: Theme Toggle + Connected Agent Badge + Connect IDE button + System Status + Reset */}
        <div className="flex items-center gap-3">
          {/* Dark / Light Mode Toggle Button */}
          <ThemeToggle />

          {/* Connected Agent Quick Badge */}
          <div
            onClick={onOpenConnectModal}
            className={`cursor-pointer hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-full border transition-all duration-200 ${
              isAgentConnected
                ? 'bg-emerald-950/20 border-emerald-500/40 hover:border-emerald-500/70 text-emerald-400 shadow-sm shadow-emerald-500/10'
                : 'bg-[var(--color-bg-primary)] border-[var(--color-border)] hover:border-cyan-500/50 text-[var(--color-text-secondary)]'
            }`}
            title="Click to manage AI IDE connections"
          >
            <Radio size={13} className={isAgentConnected ? 'animate-pulse text-emerald-400' : 'text-gray-400'} />
            <span className="text-xs font-bold">
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

