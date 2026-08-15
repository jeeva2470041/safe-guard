import { useState, useEffect, useCallback } from 'react';
import { Radio, Wifi, WifiOff, Clock, Activity, Hash } from 'lucide-react';
import { usePolling } from '../hooks/usePolling';
import { getAgentStatus } from '../services/api';

/**
 * AntigravityStatus — Real-time Antigravity connection status indicator.
 * Polls GET /api/agent/status to show actual connection state based on received events.
 * Only shows CONNECTED when real Antigravity events have been received.
 */
export default function AntigravityStatus() {
  const { data: status } = usePolling(
    useCallback(() => getAgentStatus(), []),
    3000,
    true
  );

  if (!status) {
    return (
      <div className="glass-card p-4 animate-pulse">
        <div className="h-4 bg-white/5 rounded w-1/2 mb-2" />
        <div className="h-3 bg-white/5 rounded w-3/4" />
      </div>
    );
  }

  const isConnected = status.connected;
  const lastSeen = status.lastSeenAt;
  const interceptedCount = status.interceptedCount || 0;

  // Calculate relative time
  let lastSeenText = 'Never';
  if (lastSeen) {
    const diff = Math.floor((Date.now() - new Date(lastSeen).getTime()) / 1000);
    if (diff < 5) lastSeenText = 'Just now';
    else if (diff < 60) lastSeenText = `${diff}s ago`;
    else if (diff < 3600) lastSeenText = `${Math.floor(diff / 60)}m ago`;
    else lastSeenText = `${Math.floor(diff / 3600)}h ago`;
  }

  return (
    <div className="glass-card p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-[0.65rem] font-bold uppercase tracking-wider text-[var(--color-text-muted)] flex items-center gap-1.5">
          <Radio size={12} />
          Connected Agent
        </span>
        <span
          className={`text-[0.65rem] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
            isConnected
              ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
              : 'text-gray-400 bg-gray-500/10 border-gray-500/30'
          }`}
        >
          {isConnected ? '● CONNECTED' : '○ WAITING'}
        </span>
      </div>

      {/* Agent Name */}
      <div className="flex items-center gap-2">
        {isConnected ? (
          <Wifi size={16} className="text-emerald-400" />
        ) : (
          <WifiOff size={16} className="text-gray-500" />
        )}
        <span
          className={`text-sm font-bold tracking-wider ${
            isConnected ? 'text-emerald-400' : 'text-gray-500'
          }`}
        >
          ANTIGRAVITY
        </span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-2 text-[0.7rem]">
        <div className="flex items-center gap-1.5 text-[var(--color-text-muted)]">
          <Clock size={11} />
          <span>Last Event:</span>
          <span className={`font-semibold ${isConnected ? 'text-cyan-400' : 'text-gray-500'}`}>
            {lastSeenText}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[var(--color-text-muted)]">
          <Activity size={11} />
          <span>Intercepted:</span>
          <span className="font-semibold text-cyan-400">
            {interceptedCount}
          </span>
        </div>
      </div>

      {/* Session Info */}
      {status.activeGoalId && (
        <div className="text-[0.65rem] text-[var(--color-text-muted)] border-t border-[var(--color-border)] pt-2 flex items-center gap-1.5">
          <Hash size={10} />
          <span>Session: <span className="text-cyan-400 font-mono">{status.activeSessionId?.slice(0, 8) || '—'}</span></span>
          <span className="mx-1 opacity-30">|</span>
          <span>Goal: <span className="text-cyan-400 font-mono">{status.activeGoalId}</span></span>
        </div>
      )}

      {/* Waiting state message */}
      {!isConnected && (
        <div className="text-[0.65rem] text-gray-500 border-t border-[var(--color-border)] pt-2">
          Waiting for Antigravity to send tool events via PreToolUse hook…
        </div>
      )}
    </div>
  );
}
