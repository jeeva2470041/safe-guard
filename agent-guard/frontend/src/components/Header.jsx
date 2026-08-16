import { useRef, useState, useEffect } from 'react';
import {
  Shield,
  Plus,
  Radio,
  LayoutDashboard,
  ShieldAlert,
  FlaskConical,
  FileCheck,
  Zap,
} from 'lucide-react';
import ThemeToggle from './ThemeToggle';

/**
 * Header — Premium AGENT GUARD branding with mobile-responsive layout and fluid sliding tab navigation.
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
    ACTIVE: { color: 'bg-blue-500', text: 'READY', pulse: false },
    RUNNING: { color: 'bg-emerald-500', text: 'RUNNING', pulse: true },
    WARNING: { color: 'bg-amber-500', text: 'AT RISK', pulse: true },
    PAUSED: { color: 'bg-red-500', text: 'PAUSED', pulse: true },
    WAITING_FOR_APPROVAL: { color: 'bg-amber-500', text: 'APPROVAL', pulse: true },
    BLOCKED_ACTION: { color: 'bg-red-500', text: 'BLOCKED', pulse: false },
    COMPLETED: { color: 'bg-cyan-500', text: 'DONE', pulse: false },
    FAILED: { color: 'bg-red-600', text: 'FAILED', pulse: false },
    STOPPED: { color: 'bg-gray-600', text: 'STOPPED', pulse: false },
  };

  const status = statusConfig[agentStatus] || statusConfig.IDLE;
  const isAgentConnected = Boolean(sessionStatus?.connected);

  const tabs = [
    { id: 'dashboard', label: 'SOC Dashboard', shortLabel: 'Dashboard', icon: LayoutDashboard },
    { id: 'threats', label: 'Threat Simulator', shortLabel: 'Threats', icon: ShieldAlert },
    { id: 'sandbox', label: 'Policy Sandbox', shortLabel: 'Sandbox', icon: FlaskConical },
    { id: 'compliance', label: 'Compliance & Audit', shortLabel: 'Audit', icon: FileCheck },
  ];

  // Sliding pill indicator state
  const tabRefs = useRef({});
  const [indicatorStyle, setIndicatorStyle] = useState({ left: 0, width: 0, opacity: 0 });

  useEffect(() => {
    const updateIndicator = () => {
      const activeEl = tabRefs.current[activeTab];
      if (activeEl) {
        setIndicatorStyle({
          left: activeEl.offsetLeft,
          width: activeEl.offsetWidth,
          opacity: 1,
        });
      }
    };

    updateIndicator();
    window.addEventListener('resize', updateIndicator);
    return () => window.removeEventListener('resize', updateIndicator);
  }, [activeTab]);

  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-secondary)]/95 backdrop-blur-xl sticky top-0 z-40 transition-colors duration-200 shadow-md">
      <div className="max-w-[1440px] mx-auto px-3 sm:px-6 py-2.5 sm:py-3 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Top Row on Mobile: Brand Logo + Status Controls */}
        <div className="flex items-center justify-between gap-2 min-w-0">
          {/* Logo & Title */}
          <div className="flex items-center gap-2.5 sm:gap-3.5 min-w-0">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/25 ring-1 ring-white/20 shrink-0">
              <Shield size={20} className="text-white sm:w-[22px] sm:h-[22px]" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 sm:gap-2">
                <h1 className="text-sm sm:text-base font-extrabold tracking-tight text-[var(--color-text-primary)] truncate">
                  AGENT GUARD
                </h1>
                <span className="text-[0.55rem] sm:text-[0.6rem] font-extrabold uppercase px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 tracking-wider shrink-0">
                  SOC v5.2
                </span>
              </div>
              <p className="text-[0.6rem] sm:text-[0.65rem] text-[var(--color-text-muted)] tracking-wide font-medium flex items-center gap-1.5 truncate">
                <span className="truncate">Runtime Goal Integrity</span>
                <span className="hidden sm:inline-flex items-center gap-1 text-emerald-400 font-mono text-[0.6rem] shrink-0">
                  <Zap size={10} /> ~12ms
                </span>
              </p>
            </div>
          </div>

          {/* Quick Actions (Theme + Reset on Mobile) */}
          <div className="flex items-center gap-1.5 md:hidden">
            <ThemeToggle />
            {onReset && (
              <button onClick={onReset} className="btn-reset text-[0.65rem] px-2.5 py-1">
                RESET
              </button>
            )}
          </div>
        </div>

        {/* Center: Fluid Animated Sliding Tab Navigation (Responsive Horizontal Bar) */}
        {showNav && onTabChange && (
          <div className="w-full md:w-auto overflow-x-auto no-scrollbar py-0.5">
            <nav className="relative flex items-center p-1 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)] shadow-inner w-max mx-auto md:mx-0">
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
                    className={`relative z-10 flex items-center gap-1.5 px-2.5 sm:px-3.5 py-1.5 rounded-lg text-[0.7rem] sm:text-xs font-bold transition-colors duration-200 cursor-pointer select-none whitespace-nowrap ${
                      isActive
                        ? 'text-white'
                        : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                    }`}
                  >
                    <Icon
                      size={13}
                      className={`shrink-0 transition-transform duration-200 ${
                        isActive ? 'text-white scale-105' : 'text-[var(--color-text-muted)]'
                      }`}
                    />
                    <span className="hidden lg:inline tracking-wide">{tab.label}</span>
                    <span className="inline lg:hidden tracking-wide">{tab.shortLabel}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        )}

        {/* Right Section: Desktop Controls & Status */}
        <div className="hidden md:flex items-center gap-2">
          {/* Dark / Light Mode Toggle */}
          <ThemeToggle />

          {/* Connected Agent Status Badge */}
          <div
            onClick={onOpenConnectModal}
            className={`cursor-pointer hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all duration-200 ${
              isAgentConnected
                ? 'bg-emerald-950/20 border-emerald-500/40 hover:border-emerald-500/70 text-emerald-400 shadow-sm shadow-emerald-500/10'
                : 'bg-[var(--color-bg-primary)] border-[var(--color-border)] hover:border-cyan-500/50 text-[var(--color-text-secondary)]'
            }`}
            title="Click to manage AI IDE connections"
          >
            <Radio size={12} className={isAgentConnected ? 'animate-pulse text-emerald-400' : 'text-gray-400'} />
            <span className="text-[0.7rem] font-bold">
              {isAgentConnected ? 'Antigravity Active' : 'Antigravity Standby'}
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
              className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1.5 font-bold shadow-md shadow-cyan-500/20 whitespace-nowrap"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
            >
              <Plus size={13} />
              <span>CONNECT IDE</span>
            </button>
          )}

          {/* Agent Execution State */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[var(--color-border)] bg-[var(--color-bg-primary)] shrink-0">
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
            <button onClick={onReset} className="btn-reset text-xs px-3 py-1.5">
              RESET
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
