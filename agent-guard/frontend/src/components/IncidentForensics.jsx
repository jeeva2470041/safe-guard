import { useState, useEffect, useCallback } from 'react';
import {
  ShieldAlert,
  Flame,
  KeyRound,
  TerminalSquare,
  FolderLock,
  Network,
  Cpu,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Eye,
  RefreshCw,
  Unlock,
  Check,
  ArrowRight,
  Sparkles,
  Shield,
  Layers,
  FileCode,
  Lock,
  Activity,
  History,
  Radio,
  ExternalLink,
  ChevronRight,
  Zap,
} from 'lucide-react';
import {
  getIncidents,
  getIncidentSummary,
  resolveIncident,
  unfreezeGoalAfterIncident,
} from '../services/api';

/**
 * IncidentForensics — SOC Incident & Attack Forensics Dashboard (Phase 3).
 * Multi-layer threat analysis, attack chain graphs, and runtime containment remediation.
 */
export default function IncidentForensics({ goalId, onUnfreezeSuccess, onModifyGoalRequest }) {
  const [incidents, setIncidents] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [resolvingId, setResolvingId] = useState(null);
  const [unfreezing, setUnfreezing] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);

  const fetchIncidentsData = useCallback(async () => {
    if (!goalId) return;
    try {
      const [listRes, summaryRes] = await Promise.all([
        getIncidents(goalId),
        getIncidentSummary(goalId),
      ]);
      const incList = listRes?.incidents || [];
      setIncidents(incList);
      setSummary(summaryRes);

      // Auto-select first open incident or first incident if none selected
      if (!selectedIncident && incList.length > 0) {
        const firstOpen = incList.find((i) => i.status === 'OPEN') || incList[0];
        setSelectedIncident(firstOpen);
      } else if (selectedIncident) {
        // Keep selected incident updated
        const updated = incList.find((i) => i.incidentId === selectedIncident.incidentId);
        if (updated) setSelectedIncident(updated);
      }
    } catch (err) {
      console.error('Failed to fetch incident forensics:', err);
    } finally {
      setLoading(false);
    }
  }, [goalId, selectedIncident]);

  useEffect(() => {
    fetchIncidentsData();
    const interval = setInterval(fetchIncidentsData, 2000);
    return () => clearInterval(interval);
  }, [fetchIncidentsData]);

  const handleResolve = async (incidentId, e) => {
    if (e) e.stopPropagation();
    setResolvingId(incidentId);
    try {
      await resolveIncident(incidentId);
      setActionMessage({ type: 'success', text: `Incident ${incidentId} marked as resolved.` });
      await fetchIncidentsData();
    } catch (err) {
      setActionMessage({ type: 'error', text: `Failed to resolve incident: ${err.message}` });
    } finally {
      setResolvingId(null);
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const handleUnfreezeGoal = async () => {
    setUnfreezing(true);
    try {
      await unfreezeGoalAfterIncident(goalId);
      setActionMessage({ type: 'success', text: 'Agent successfully unfreezed and resumed to ACTIVE.' });
      if (onUnfreezeSuccess) onUnfreezeSuccess();
      await fetchIncidentsData();
    } catch (err) {
      setActionMessage({ type: 'error', text: `Failed to unfreeze agent: ${err.message}` });
    } finally {
      setUnfreezing(false);
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  // 7-Layer Threat Intelligence Status Data
  const threatLayers = [
    {
      id: 'prompt_injection',
      name: 'Prompt Injection Guard',
      icon: Flame,
      color: 'from-red-500 to-rose-600',
      activeCount: incidents.filter((i) => i.attackType === 'PROMPT_INJECTION' && i.status === 'OPEN').length,
      totalCount: incidents.filter((i) => i.attackType === 'PROMPT_INJECTION').length,
      desc: 'Structural, Indirect DOM & Obfuscated Injections',
      owasp: 'OWASP LLM01',
    },
    {
      id: 'goal_hijacking',
      name: 'Goal Hijacking Engine',
      icon: Activity,
      color: 'from-amber-500 to-orange-600',
      activeCount: incidents.filter((i) => i.attackType === 'GOAL_HIJACKING' && i.status === 'OPEN').length,
      totalCount: incidents.filter((i) => i.attackType === 'GOAL_HIJACKING').length,
      desc: 'Domain Jump & Trajectory Drift Detection',
      owasp: 'OWASP LLM06',
    },
    {
      id: 'credential_guard',
      name: 'Credential Guard',
      icon: KeyRound,
      color: 'from-red-600 to-pink-600',
      activeCount: incidents.filter((i) => i.attackType === 'CREDENTIAL_THEFT' && i.status === 'OPEN').length,
      totalCount: incidents.filter((i) => i.attackType === 'CREDENTIAL_THEFT').length,
      desc: '.env, SSH Keys, Cookies & Cloud Tokens',
      owasp: 'OWASP LLM06',
    },
    {
      id: 'shell_security',
      name: 'Shell Security Guard',
      icon: TerminalSquare,
      color: 'from-purple-500 to-indigo-600',
      activeCount: incidents.filter((i) => i.attackType === 'DESTRUCTIVE_ATTACK' && i.status === 'OPEN').length,
      totalCount: incidents.filter((i) => i.attackType === 'DESTRUCTIVE_ATTACK').length,
      desc: 'Destructive Commands, Reverse Shells & Pipe-to-Bash',
      owasp: 'OWASP LLM08',
    },
    {
      id: 'filesystem_guard',
      name: 'Filesystem Guard',
      icon: FolderLock,
      color: 'from-cyan-500 to-blue-600',
      activeCount: incidents.filter((i) => i.attackType === 'PATH_TRAVERSAL' && i.status === 'OPEN').length,
      totalCount: incidents.filter((i) => i.attackType === 'PATH_TRAVERSAL').length,
      desc: 'Path Traversal & Sandbox Escape Prevention',
      owasp: 'OWASP LLM08',
    },
    {
      id: 'exfiltration_guard',
      name: 'Exfiltration Guard',
      icon: Network,
      color: 'from-emerald-500 to-teal-600',
      activeCount: incidents.filter((i) => i.attackType === 'DATA_EXFILTRATION' && i.status === 'OPEN').length,
      totalCount: incidents.filter((i) => i.attackType === 'DATA_EXFILTRATION').length,
      desc: 'Sensitive Read -> Encode -> Outbound Transfer Links',
      owasp: 'OWASP LLM02',
    },
    {
      id: 'mcp_security',
      name: 'MCP Security Engine',
      icon: Cpu,
      color: 'from-blue-600 to-indigo-700',
      activeCount: incidents.filter((i) => i.attackType === 'MCP_TOOL_POISONING' && i.status === 'OPEN').length,
      totalCount: incidents.filter((i) => i.attackType === 'MCP_TOOL_POISONING').length,
      desc: 'Tool Poisoning & Fail-Closed Capability Policy',
      owasp: 'OWASP LLM07',
    },
  ];

  const filteredIncidents = incidents.filter((inc) => {
    if (filterSeverity !== 'ALL' && inc.severity !== filterSeverity) return false;
    if (filterStatus !== 'ALL' && inc.status !== filterStatus) return false;
    return true;
  });

  const getAttackTypeBadge = (type) => {
    switch (type) {
      case 'CREDENTIAL_THEFT':
        return { label: 'Credential Theft', color: 'bg-red-500/10 text-red-400 border-red-500/30', icon: KeyRound };
      case 'PROMPT_INJECTION':
        return { label: 'Prompt Injection', color: 'bg-rose-500/10 text-rose-400 border-rose-500/30', icon: Flame };
      case 'PATH_TRAVERSAL':
        return { label: 'Path Traversal', color: 'bg-purple-500/10 text-purple-400 border-purple-500/30', icon: FolderLock };
      case 'DATA_EXFILTRATION':
        return { label: 'Data Exfiltration', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', icon: Network };
      case 'DESTRUCTIVE_ATTACK':
        return { label: 'Destructive Shell', color: 'bg-amber-500/10 text-amber-400 border-amber-500/30', icon: TerminalSquare };
      case 'GOAL_HIJACKING':
        return { label: 'Goal Hijacking', color: 'bg-orange-500/10 text-orange-400 border-orange-500/30', icon: Activity };
      default:
        return { label: type || 'Security Violation', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30', icon: ShieldAlert };
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border-red-500/40 shadow-red-500/20';
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40 shadow-amber-500/20';
      case 'MEDIUM':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/40 shadow-blue-500/20';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/40';
    }
  };

  return (
    <div className="space-y-6">
      {/* Action Notification Alert */}
      {actionMessage && (
        <div
          className={`p-3.5 rounded-xl border flex items-center justify-between text-xs font-semibold animate-fade-in ${
            actionMessage.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
              : 'bg-red-950/40 border-red-500/40 text-red-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {actionMessage.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
            <span>{actionMessage.text}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="text-gray-400 hover:text-white">
            <XCircle size={14} />
          </button>
        </div>
      )}

      {/* Top Banner & High-Level SOC Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4 rounded-2xl bg-gradient-to-br from-red-950/30 via-transparent to-transparent border border-red-500/30 shadow-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 rounded-full blur-2xl pointer-events-none" />
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-red-400 flex items-center gap-1.5">
              <ShieldAlert size={14} className="animate-pulse" />
              Open Incidents
            </span>
            <span className="text-[0.65rem] px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/40 font-mono font-bold">
              {summary?.open || 0} ACTIVE
            </span>
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">
            {summary?.open || 0}
          </div>
          <p className="text-[0.7rem] text-[var(--color-text-muted)] mt-1">
            {summary?.hasCriticalThreat ? 'Critical threats require remediation' : 'No active critical blocks'}
          </p>
        </div>

        <div className="card p-4 rounded-2xl bg-gradient-to-br from-emerald-950/30 via-transparent to-transparent border border-emerald-500/30 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 size={14} />
              Resolved Incidents
            </span>
            <span className="text-[0.65rem] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-mono font-bold">
              {summary?.resolved || 0} RESOLVED
            </span>
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">
            {summary?.resolved || 0}
          </div>
          <p className="text-[0.7rem] text-[var(--color-text-muted)] mt-1">
            Contained and verified threats
          </p>
        </div>

        <div className="card p-4 rounded-2xl bg-gradient-to-br from-cyan-950/30 via-transparent to-transparent border border-cyan-500/30 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
              <Layers size={14} />
              Total Incidents
            </span>
            <span className="text-[0.65rem] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 font-mono font-bold">
              ALL TIME
            </span>
          </div>
          <div className="text-3xl font-extrabold text-white mt-2">
            {summary?.total || 0}
          </div>
          <p className="text-[0.7rem] text-[var(--color-text-muted)] mt-1">
            {summary?.severity?.CRITICAL || 0} Critical &bull; {summary?.severity?.HIGH || 0} High
          </p>
        </div>

        <div className="card p-4 rounded-2xl bg-gradient-to-br from-indigo-950/30 via-transparent to-transparent border border-indigo-500/30 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
              <Unlock size={14} />
              Containment Controls
            </span>
            <span className="text-[0.65rem] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 font-mono font-bold">
              REMEDY
            </span>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <button
              onClick={handleUnfreezeGoal}
              disabled={unfreezing}
              className="flex-1 btn-primary py-2 px-3 text-xs font-bold flex items-center justify-center gap-1.5 shadow-md shadow-cyan-500/20"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
              title="Unfreeze agent from containment pause"
            >
              <Unlock size={13} className={unfreezing ? 'animate-spin' : ''} />
              <span>{unfreezing ? 'Unfreezing...' : 'Unfreeze Agent'}</span>
            </button>
            {onModifyGoalRequest && (
              <button
                onClick={onModifyGoalRequest}
                className="btn-secondary py-2 px-2.5 text-xs font-bold text-gray-300 hover:text-white"
                title="Update policy constraints"
              >
                Modify Goal
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 7-Layer Threat Intelligence Matrix */}
      <div className="card p-5 rounded-2xl border border-[var(--color-border)] shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--color-border)] pb-3">
          <div>
            <h2 className="text-sm font-extrabold text-[var(--color-text-primary)] flex items-center gap-2">
              <Zap size={16} className="text-cyan-400" />
              7-Layer Real-Time Threat Intelligence Matrix
            </h2>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
              Continuous runtime behavioral telemetry across all 7 autonomous agent defense layers.
            </p>
          </div>
          <span className="text-[0.65rem] font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 w-fit">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            7/7 LAYERS ACTIVE &amp; ENFORCING
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {threatLayers.map((layer) => {
            const Icon = layer.icon;
            const hasActive = layer.activeCount > 0;
            return (
              <div
                key={layer.id}
                className={`p-3.5 rounded-xl border transition-all duration-200 ${
                  hasActive
                    ? 'bg-red-950/20 border-red-500/50 shadow-md shadow-red-500/10'
                    : 'bg-[var(--color-bg-primary)] border-[var(--color-border)] hover:border-cyan-500/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-7 h-7 rounded-lg bg-gradient-to-br ${layer.color} flex items-center justify-center text-white shadow-sm`}
                    >
                      <Icon size={14} />
                    </div>
                    <span className="text-xs font-bold text-[var(--color-text-primary)] truncate">
                      {layer.name}
                    </span>
                  </div>
                  <span
                    className={`text-[0.6rem] font-mono font-bold px-1.5 py-0.5 rounded border ${
                      hasActive
                        ? 'bg-red-500/20 text-red-400 border-red-500/40 animate-pulse'
                        : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    }`}
                  >
                    {hasActive ? `${layer.activeCount} BLOCKED` : 'PROTECTED'}
                  </span>
                </div>
                <p className="text-[0.65rem] text-[var(--color-text-muted)] mt-2 line-clamp-2 leading-relaxed">
                  {layer.desc}
                </p>
                <div className="mt-2.5 pt-2 border-t border-[var(--color-border)]/60 flex items-center justify-between text-[0.6rem] text-[var(--color-text-muted)]">
                  <span className="font-mono text-cyan-400">{layer.owasp}</span>
                  <span>{layer.totalCount} total intercepted</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main 2-Column Incident Forensics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 Cols) — Incident Feed & Filters */}
        <div className="lg:col-span-5 space-y-4">
          <div className="card p-4 rounded-2xl border border-[var(--color-border)] shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-extrabold uppercase tracking-wider text-[var(--color-text-primary)] flex items-center gap-1.5">
                <Radio size={14} className="text-red-400 animate-pulse" />
                Security Incident Feed
              </h3>
              <button
                onClick={fetchIncidentsData}
                className="text-[0.7rem] text-gray-400 hover:text-cyan-400 flex items-center gap-1 transition-colors"
                title="Refresh incident list"
              >
                <RefreshCw size={11} className={loading ? 'animate-spin' : ''} />
                <span>Refresh</span>
              </button>
            </div>

            {/* Filter Chips */}
            <div className="flex flex-wrap items-center gap-1.5 text-[0.65rem]">
              <span className="text-[var(--color-text-muted)] font-medium mr-1">Severity:</span>
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'].map((sev) => (
                <button
                  key={sev}
                  onClick={() => setFilterSeverity(sev)}
                  className={`px-2 py-0.5 rounded-md font-bold transition-all ${
                    filterSeverity === sev
                      ? 'bg-cyan-500 text-black shadow-sm shadow-cyan-500/30'
                      : 'bg-[var(--color-bg-primary)] text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:border-cyan-500/50'
                  }`}
                >
                  {sev}
                </button>
              ))}

              <span className="text-[var(--color-text-muted)] font-medium ml-2 mr-1">Status:</span>
              {['ALL', 'OPEN', 'RESOLVED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  className={`px-2 py-0.5 rounded-md font-bold transition-all ${
                    filterStatus === st
                      ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30'
                      : 'bg-[var(--color-bg-primary)] text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:border-blue-500/50'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            {/* Incident List Items */}
            <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1 no-scrollbar">
              {filteredIncidents.length === 0 ? (
                <div className="text-center py-10 text-[var(--color-text-muted)] text-xs">
                  <ShieldCheck size={32} className="mx-auto text-emerald-400 mb-2 opacity-80" />
                  <p className="font-bold">No security incidents matching current filters.</p>
                  <p className="text-[0.65rem] mt-1">All agent actions are safely aligned with policy.</p>
                </div>
              ) : (
                filteredIncidents.map((inc) => {
                  const isSelected = selectedIncident?.incidentId === inc.incidentId;
                  const attackBadge = getAttackTypeBadge(inc.attackType);
                  const AttackIcon = attackBadge.icon;
                  const isOpen = inc.status === 'OPEN';

                  return (
                    <div
                      key={inc.incidentId}
                      onClick={() => setSelectedIncident(inc)}
                      className={`p-3.5 rounded-xl border transition-all duration-200 cursor-pointer text-left relative overflow-hidden ${
                        isSelected
                          ? 'bg-gradient-to-r from-blue-950/40 via-cyan-950/20 to-[var(--color-bg-secondary)] border-cyan-500/70 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/40'
                          : 'bg-[var(--color-bg-primary)] border-[var(--color-border)] hover:border-cyan-500/40'
                      }`}
                    >
                      {/* Left accent color bar */}
                      <div
                        className={`absolute left-0 top-0 bottom-0 w-1 ${
                          isOpen ? (inc.severity === 'CRITICAL' ? 'bg-red-500' : 'bg-amber-500') : 'bg-emerald-500'
                        }`}
                      />

                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="font-mono text-[0.7rem] font-extrabold text-cyan-400">
                            {inc.incidentId}
                          </span>
                          <span
                            className={`text-[0.6rem] font-bold px-1.5 py-0.5 rounded border ${attackBadge.color} flex items-center gap-1 truncate`}
                          >
                            <AttackIcon size={10} />
                            {attackBadge.label}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 shrink-0">
                          <span
                            className={`text-[0.6rem] font-bold px-1.5 py-0.5 rounded border ${getSeverityBadge(
                              inc.severity
                            )}`}
                          >
                            {inc.severity}
                          </span>
                          <span
                            className={`text-[0.6rem] font-bold px-1.5 py-0.5 rounded ${
                              isOpen
                                ? 'bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse'
                                : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            }`}
                          >
                            {inc.status}
                          </span>
                        </div>
                      </div>

                      <div className="mt-2 text-xs font-semibold text-[var(--color-text-primary)] truncate">
                        Target: <span className="font-mono text-amber-300 font-normal">{inc.target || 'N/A'}</span>
                      </div>

                      <p className="text-[0.65rem] text-[var(--color-text-muted)] mt-1 line-clamp-2 leading-relaxed">
                        {inc.triggerReason || 'Adversarial tool invocation intercepted by Agent Guard.'}
                      </p>

                      <div className="mt-2.5 pt-2 border-t border-[var(--color-border)]/50 flex items-center justify-between text-[0.6rem] text-[var(--color-text-muted)]">
                        <span>{new Date(inc.createdAt || Date.now()).toLocaleTimeString()}</span>
                        <div className="flex items-center gap-2">
                          {isOpen && (
                            <button
                              onClick={(e) => handleResolve(inc.incidentId, e)}
                              disabled={resolvingId === inc.incidentId}
                              className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/40 font-bold transition-all"
                            >
                              {resolvingId === inc.incidentId ? 'Resolving...' : 'Resolve'}
                            </button>
                          )}
                          <span className="text-cyan-400 font-bold flex items-center gap-0.5">
                            Inspect <ChevronRight size={10} />
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Column (7 Cols) — Interactive Attack Chain Visualizer & Deep Forensic Inspection */}
        <div className="lg:col-span-7 space-y-4">
          {selectedIncident ? (
            <div className="card p-5 rounded-2xl border border-[var(--color-border)] shadow-xl space-y-5">
              {/* Incident Header & Action Controls */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--color-border)] pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-base font-extrabold text-cyan-400">
                      {selectedIncident.incidentId}
                    </span>
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded border ${getSeverityBadge(
                        selectedIncident.severity
                      )}`}
                    >
                      {selectedIncident.severity}
                    </span>
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded ${
                        selectedIncident.status === 'OPEN'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      }`}
                    >
                      {selectedIncident.status}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--color-text-muted)] mt-1">
                    Containment Action:{' '}
                    <span className="font-bold text-red-400 font-mono">
                      {selectedIncident.containmentAction || 'AGENT_FROZEN'}
                    </span>{' '}
                    &bull; Recorded at{' '}
                    {new Date(selectedIncident.createdAt || Date.now()).toLocaleString()}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  {selectedIncident.status === 'OPEN' && (
                    <button
                      onClick={() => handleResolve(selectedIncident.incidentId)}
                      disabled={resolvingId === selectedIncident.incidentId}
                      className="btn-primary text-xs px-3.5 py-1.5 font-bold flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-500/20"
                    >
                      <Check size={13} />
                      <span>{resolvingId === selectedIncident.incidentId ? 'Resolving...' : 'Resolve Incident'}</span>
                    </button>
                  )}
                  <button
                    onClick={handleUnfreezeGoal}
                    disabled={unfreezing}
                    className="btn-secondary text-xs px-3.5 py-1.5 font-bold flex items-center gap-1.5 text-cyan-400 hover:text-cyan-300 border border-cyan-500/40"
                  >
                    <Unlock size={13} />
                    <span>Unfreeze</span>
                  </button>
                </div>
              </div>

              {/* Interactive Attack Chain Directed Graph */}
              <div className="p-4 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)] space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-extrabold uppercase tracking-wider text-[var(--color-text-primary)] flex items-center gap-2">
                    <Sparkles size={14} className="text-cyan-400" />
                    Multi-Step Attack Kill-Chain Graph
                  </h4>
                  <span className="text-[0.6rem] font-mono text-gray-400">
                    {selectedIncident.attackChain?.nodeCount || (selectedIncident.attackChain?.nodes?.length ?? 1)} NODES
                  </span>
                </div>

                {/* Kill Chain Flow Steps */}
                <div className="p-3 rounded-lg bg-[var(--color-bg-secondary)] border border-[var(--color-border)]/60 overflow-x-auto no-scrollbar">
                  <div className="flex items-center gap-2 min-w-max py-2">
                    {selectedIncident.attackChain?.nodes && selectedIncident.attackChain.nodes.length > 0 ? (
                      selectedIncident.attackChain.nodes.map((node, idx) => (
                        <div key={node.nodeId || idx} className="flex items-center gap-2">
                          <div className="p-2.5 rounded-xl border border-red-500/40 bg-gradient-to-br from-red-950/40 to-[var(--color-bg-primary)] shadow-md min-w-[170px] max-w-[200px]">
                            <div className="flex items-center justify-between text-[0.6rem]">
                              <span className="font-mono text-cyan-400 font-bold">
                                {node.roleInAttack || `STAGE ${idx + 1}`}
                              </span>
                              <span className="px-1.5 py-0.2 rounded bg-red-500/20 text-red-300 font-bold">
                                {node.decision || 'BLOCK'}
                              </span>
                            </div>
                            <div className="text-xs font-bold text-white mt-1 truncate">
                              {node.actionType || 'INTERCEPTED_ACTION'}
                            </div>
                            <div className="text-[0.65rem] text-amber-300 font-mono truncate mt-0.5">
                              {node.target || 'target'}
                            </div>
                          </div>

                          {idx < selectedIncident.attackChain.nodes.length - 1 && (
                            <div className="flex flex-col items-center justify-center px-1 text-cyan-400">
                              <ArrowRight size={16} className="animate-pulse text-red-400" />
                              <span className="text-[0.55rem] font-mono text-[var(--color-text-muted)]">
                                {selectedIncident.attackChain?.edges?.[idx]?.relation || 'escalates'}
                              </span>
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      // Single Node Containment Fallback Graph
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl border border-cyan-500/40 bg-cyan-950/20 shadow-md min-w-[160px]">
                          <div className="text-[0.6rem] font-mono text-cyan-400 font-bold">STAGE 1: VECTOR</div>
                          <div className="text-xs font-bold text-white mt-1">
                            {selectedIncident.actionType || 'PROPOSED_ACTION'}
                          </div>
                          <div className="text-[0.65rem] text-amber-300 font-mono truncate mt-0.5">
                            {selectedIncident.target || 'Target Resource'}
                          </div>
                        </div>

                        <ArrowRight size={16} className="text-red-400 animate-pulse" />

                        <div className="p-2.5 rounded-xl border border-red-500/50 bg-red-950/40 shadow-md min-w-[180px]">
                          <div className="flex items-center justify-between text-[0.6rem]">
                            <span className="font-mono text-red-400 font-bold">GATEWAY INTERCEPTION</span>
                            <span className="px-1.5 py-0.2 rounded bg-red-500 text-black font-extrabold">
                              BLOCKED
                            </span>
                          </div>
                          <div className="text-xs font-bold text-white mt-1">Autonomous Containment</div>
                          <div className="text-[0.65rem] text-red-300 mt-0.5">Agent Frozen (PAUSED)</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Forensic Evidence & Breakdown */}
              <div className="space-y-3">
                <h4 className="text-xs font-extrabold uppercase tracking-wider text-[var(--color-text-primary)] flex items-center gap-2">
                  <FileCode size={14} className="text-amber-400" />
                  Forensic Telemetry Evidence
                </h4>

                <div className="p-3.5 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)] space-y-2 text-xs">
                  <div className="flex items-start gap-2">
                    <span className="text-[var(--color-text-muted)] font-bold shrink-0 w-24">Trigger:</span>
                    <span className="text-red-300 font-semibold leading-relaxed">
                      {selectedIncident.triggerReason || 'Severe security violation detected.'}
                    </span>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="text-[var(--color-text-muted)] font-bold shrink-0 w-24">Target Payload:</span>
                    <span className="font-mono text-amber-300 bg-amber-950/30 px-2 py-0.5 rounded border border-amber-500/30 truncate">
                      {selectedIncident.target || 'N/A'}
                    </span>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="text-[var(--color-text-muted)] font-bold shrink-0 w-24">Action Type:</span>
                    <span className="font-mono text-cyan-300 bg-cyan-950/30 px-2 py-0.5 rounded border border-cyan-500/30">
                      {selectedIncident.actionType || 'FILE_READ'}
                    </span>
                  </div>

                  {selectedIncident.evidence && selectedIncident.evidence.length > 0 && (
                    <div className="pt-2 border-t border-[var(--color-border)]/50">
                      <span className="text-[var(--color-text-muted)] font-bold block mb-1">
                        Detected Attack Artifacts:
                      </span>
                      <ul className="space-y-1 text-[0.7rem] text-gray-300">
                        {selectedIncident.evidence.map((ev, idx) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span className="text-red-400 mt-0.5">&bull;</span>
                            <span className="font-mono leading-relaxed">{ev}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Remediation Guidance */}
              <div className="p-3.5 rounded-xl bg-gradient-to-r from-blue-950/30 via-indigo-950/20 to-transparent border border-blue-500/30 flex items-start gap-3">
                <Shield className="text-blue-400 shrink-0 mt-0.5" size={18} />
                <div className="text-xs space-y-1">
                  <div className="font-bold text-white">Recommended Security Engineer Action</div>
                  <p className="text-[0.7rem] text-[var(--color-text-muted)] leading-relaxed">
                    Verify whether the prompt injection vector originated from untrusted web retrieval or tool poisoning.
                    Once validated, resolve the incident and unfreeze the agent or adjust the goal constraints policy.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="card p-12 rounded-2xl border border-[var(--color-border)] shadow-xl text-center space-y-3">
              <ShieldCheck size={48} className="mx-auto text-cyan-400 opacity-80" />
              <h3 className="text-base font-extrabold text-white">No Incident Selected</h3>
              <p className="text-xs text-[var(--color-text-muted)] max-w-sm mx-auto">
                Select an incident from the security feed on the left to inspect its multi-step attack chain and telemetry evidence.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
