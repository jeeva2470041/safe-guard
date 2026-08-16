import { useRef, useState, useEffect } from 'react';
import {
  Shield,
  Plus,
  Radio,
  Sparkles,
  LayoutDashboard,
  ShieldAlert,
  FlaskConical,
  FileCheck,
  Zap,
} from 'lucide-react';
import ThemeToggle from './ThemeToggle';

/**
 * Header — Premium AGENT GUARD branding with live agent status, smooth sliding tab navigation, Theme Toggle, and Connect IDE controls.
 */
export default function Header({
  agentStatus = 'IDLE',
  onReset,
  sessionStatus,
  onOpenConnectModal,
  activeTab = 'dashboard',
  onTabChange,
  showNav = true,
}) {
  const statusConfig = {
    IDLE: { color: 'bg-gray-500', text: 'IDLE', pulse: false },
    ACTIVE: { color: 'bg-blue-500', text: 'AGENT READY', pulse: false },
    RUNNING: { color: 'bg-emerald-500', text: 'AGENT RUNNING', pulse: true },
    WARNING: { color: 'bg-amber-500', text: 'AGENT AT RISK', pulse: true },
    PAUSED: { color: 'bg-red-500', text: 'AGENT PAUSED', pulse: true },
    WAITING_FOR_APPROVAL: { color: 'bg-amber-500', text: 'APPROVAL NEEDED', pulse: true },
    BLOCKED_ACTION: { color: 'bg-red-500', text: 'ACTION BLOCKED', pulse: false },
    COMPLETED: { color: 'bg-cyan-500', text: 'GOAL COMPLETED', pulse: false },
    FAILED: { color: 'bg-red-600', text: 'AGENT FAILED', pulse: false },
    STOPPED: { color: 'bg-gray-600', text: 'AGENT STOPPED', pulse: false },
  };

  const status = statusConfig[agentStatus] || statusConfig.IDLE;
  const isAgentConnected = Boolean(sessionStatus?.connected);

  const tabs = [
    { id: 'dashboard', label: 'SOC Dashboard', icon: LayoutDashboard },
    { id: 'threats', label: 'Threat Simulator', icon: ShieldAlert },
    { id: 'sandbox', label: 'Policy Sandbox', icon: FlaskConical },
    { id: 'compliance', label: 'Compliance & Audit', icon: FileCheck },
  ];

  // Sliding pill indicator state
  const tabRefs = useRef({});
  const [indicatorStyle, setIndicatorStyle] = useState({ left: 0, width: 0, opacity: 0 });

  useEffect(() => {
    const activeEl = tabRefs.current[activeTab];
    if (activeEl) {
      setIndicatorStyle({
        left: activeEl.offsetLeft,
        width: activeEl.offsetWidth,
        opacity: 1,
      });
    }
  }, [activeTab]);

  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)]/95 backdrop-blur-xl sticky top-0 z-40 transition-colors duration-200 shadow-md">
      <div className="max-w-[1440px] mx-auto px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Logo & Title */}
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/25 ring-1 ring-white/20 shrink-0">
            <Shield size={22} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold tracking-tight text-[var(--color-text-primary)]">
                AGENT GUARD
              </h1>
              <span className="text-[0.6rem] font-extrabold uppercase px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 tracking-wider">
                SOC v5.2
              </span>
            </div>
            <p className="text-[0.65rem] text-[var(--color-text-muted)] tracking-wide font-medium flex items-center gap-2">
              <span>Runtime Goal Integrity & Security Gateway</span>
              <span className="hidden md:inline-flex items-center gap-1 text-emerald-400 font-mono text-[0.6rem]">
                <Zap size={10} /> ~12ms Interception
              </span>
            </p>
          </div>
        </div>

        {/* Center: Fluid Animated Sliding Tab Navigation */}
        {showNav && onTabChange && (
          <nav className="relative flex items-center p-1 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)] shadow-inner">
            {/* Smooth Sliding Pill Indicator */}
            <div
              className="absolute top-1 bottom-1 rounded-lg bg-gradient-to-r from-blue-600 via-cyan-600 to-blue-500 shadow-md shadow-blue-500/30 transition-all duration-300 ease-[cubic-bezier(0.25,1,0.5,1)] pointer-events-none"
              style={{
                left: `${indicatorStyle.left}px`,
                width: `${indicatorStyle.width}px`,
                opacity: indicatorStyle.opacity,
              }}
            />

            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  ref={(el) => (tabRefs.current[tab.id] = el)}
                  onClick={() => onTabChange(tab.id)}
                  className={`relative z-10 flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-colors duration-200 cursor-pointer select-none ${
                    isActive
                      ? 'text-white'
                      : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                  }`}
                >
                  <Icon
                    size={14}
                    className={`transition-transform duration-200 ${
                      isActive ? 'text-white scale-105' : 'text-[var(--color-text-muted)] group-hover:text-white'
                    }`}
                  />
                  <span className="hidden sm:inline tracking-wide">{tab.label}</span>
                </button>
              );
            })}
          </nav>
        )}

        {/* Right Section: Controls & Status */}
        <div className="flex items-center gap-2.5">
          {/* Dark / Light Mode Toggle */}
          <ThemeToggle />

          {/* Connected Agent Status Badge */}
          <div
            onClick={onOpenConnectModal}
            className={`cursor-pointer hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all duration-200 ${
              isAgentConnected
                ? 'bg-emerald-950/20 border-emerald-500/40 hover:border-emerald-500/70 text-emerald-400 shadow-sm shadow-emerald-500/10'
                : 'bg-[var(--color-bg-primary)] border-[var(--color-border)] hover:border-cyan-500/50 text-[var(--color-text-secondary)]'
            }`}
            title="Click to manage AI IDE connections"
          >
            <Radio size={12} className={isAgentConnected ? 'animate-pulse text-emerald-400' : 'text-gray-400'} />
            <span className="text-[0.7rem] font-bold">
              {isAgentConnected ? 'Antigravity Hook Active' : 'Antigravity Standby'}
            </span>
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isAgentConnected ? 'bg-emerald-400 animate-ping' : 'bg-gray-500'
              }`}
            />
          </div>

          {/* Connect IDE Button */}
          {onOpenConnectModal && (
            <button
              onClick={onOpenConnectModal}
              className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1.5 font-bold shadow-md shadow-cyan-500/20"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
            >
              <Plus size={13} />
              <span className="hidden sm:inline">CONNECT IDE</span>
            </button>
          )}

          {/* Agent Execution State */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-[var(--color-border)] bg-[var(--color-bg-primary)]">
            <span
              className={`w-2 h-2 rounded-full ${status.color} ${
                status.pulse ? 'animate-status-dot' : ''
              }`}
            />
            <span className="text-[0.7rem] font-semibold tracking-wider text-[var(--color-text-secondary)]">
              {status.text}
            </span>
          </div>

          {onReset && (
            <button onClick={onReset} className="btn-reset text-xs">
              RESET
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
