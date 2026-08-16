import { useState, useEffect } from 'react';
import { ShieldCheck, Eye, Lock, Sparkles } from 'lucide-react';

/**
 * GuardModeToggle — Global interactive switch for Security Guard Mode.
 * Options:
 * - ENFORCE (Active Guard): Intercepts, enforces constraints, blocks violations & requires approval.
 * - MONITOR (Audit Mode): Passive background observation, telemetry logging & non-blocking audit trail.
 */
export default function GuardModeToggle({ className = '', onChange }) {
  const [mode, setMode] = useState(() => {
    return localStorage.getItem('agent_guard_mode') || 'ENFORCE';
  });

  const handleToggle = (newMode) => {
    setMode(newMode);
    localStorage.setItem('agent_guard_mode', newMode);
    if (onChange) onChange(newMode);
  };

  useEffect(() => {
    if (onChange) onChange(mode);
  }, [mode, onChange]);

  return (
    <div className={`flex items-center gap-1.5 p-1 rounded-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] shadow-inner ${className}`}>
      {/* Enforce Mode Button */}
      <button
        type="button"
        onClick={() => handleToggle('ENFORCE')}
        className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-wide transition-all duration-200 ${
          mode === 'ENFORCE'
            ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/25 scale-[1.02]'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
        }`}
        title="Enforce Mode: Actively authorizes actions, blocks constraint violations, and requests approvals"
      >
        <ShieldCheck size={13} className={mode === 'ENFORCE' ? 'text-white' : 'text-gray-400'} />
        <span>ENFORCE</span>
      </button>

      {/* Monitor Mode Button */}
      <button
        type="button"
        onClick={() => handleToggle('MONITOR')}
        className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-wide transition-all duration-200 ${
          mode === 'MONITOR'
            ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-md shadow-amber-500/25 scale-[1.02]'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
        }`}
        title="Monitor Mode: Passive security telemetry & audit logging without blocking actions"
      >
        <Eye size={13} className={mode === 'MONITOR' ? 'text-white' : 'text-gray-400'} />
        <span>MONITOR</span>
      </button>
    </div>
  );
}
