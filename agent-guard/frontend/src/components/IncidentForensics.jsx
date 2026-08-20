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
  Play,
  RotateCcw,
  Ban,
  FileCheck,
  GitBranch,
  Copy,
  Sliders,
  Database,
} from 'lucide-react';
import {
  getIncidents,
  getIncidentSummary,
  getIncidentDetail,
  getForensicExplanation,
  resolveIncident,
  recoverIncident,
  unfreezeGoalAfterIncident,
  getCheckpoints,
  createCheckpoint,
  rollbackCheckpoint,
  verifyAuditChain,
} from '../services/api';
import SessionReplayModal from './SessionReplayModal';

/**
 * IncidentForensics — SOC Incident & Attack Forensics Dashboard (Phase 3 & 4).
 * Multi-layer threat analysis, attack chain graphs, blast radius calculation,
 * 10-point "WHY BLOCKED" forensic explanations, 5-option recovery, and tamper-evident audit verification.
 */
export default function IncidentForensics({ goalId, onUnfreezeSuccess, onModifyGoalRequest }) {
  const [incidents, setIncidents] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [forensicExplanation, setForensicExplanation] = useState(null);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [actionMessage, setActionMessage] = useState(null);
  const [copiedText, setCopiedText] = useState(false);

  // Phase 4 states
  const [replayModalOpen, setReplayModalOpen] = useState(false);
  const [checkpoints, setCheckpoints] = useState([]);
  const [checkpointsOpen, setCheckpointsOpen] = useState(false);
  const [auditVerification, setAuditVerification] = useState(null);
  const [verifyingAudit, setVerifyingAudit] = useState(false);
  const [recoveryLoading, setRecoveryLoading] = useState(false);
  const [selectedCheckpointForRollback, setSelectedCheckpointForRollback] = useState('');
  const [evolveGoalText, setEvolveGoalText] = useState('');
  const [evolveModalOpen, setEvolveModalOpen] = useState(false);

  const fetchIncidentsData = useCallback(async () => {
    if (!goalId) return;
    try {
      const [listRes, summaryRes, chkRes] = await Promise.all([
        getIncidents(goalId),
        getIncidentSummary(goalId),
        getCheckpoints(goalId).catch(() => ({ checkpoints: [] })),
      ]);
      const incList = listRes?.incidents || [];
      setIncidents(incList);
      setSummary(summaryRes);
      setCheckpoints(chkRes?.checkpoints || []);

      // Auto-select first open incident or first incident if none selected
      if (!selectedIncident && incList.length > 0) {
        const firstOpen = incList.find((i) => i.status === 'OPEN') || incList[0];
        setSelectedIncident(firstOpen);
      } else if (selectedIncident) {
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

  // Fetch 10-point forensic explanation whenever selected incident changes
  useEffect(() => {
    if (selectedIncident?.incidentId) {
      getForensicExplanation(selectedIncident.incidentId)
        .then((exp) => setForensicExplanation(exp))
        .catch(() => setForensicExplanation(null));
    }
  }, [selectedIncident]);

  const handleResolve = async (incidentId, e) => {
    if (e) e.stopPropagation();
    try {
      await resolveIncident(incidentId);
      setActionMessage({ type: 'success', text: `Incident ${incidentId} marked as resolved.` });
      await fetchIncidentsData();
    } catch (err) {
      setActionMessage({ type: 'error', text: `Failed to resolve incident: ${err.message}` });
    } finally {
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const handleExecuteRecovery = async (recoveryAction, params = {}) => {
    if (!selectedIncident) return;
    setRecoveryLoading(true);
    try {
      const res = await recoverIncident(selectedIncident.incidentId, recoveryAction, params);
      setActionMessage({
        type: 'success',
        text: `Recovery '${recoveryAction}' executed successfully: ${res.result?.message || 'Done'}`,
      });
      if (recoveryAction === 'CONTINUE' && onUnfreezeSuccess) {
        onUnfreezeSuccess();
      }
      setEvolveModalOpen(false);
      await fetchIncidentsData();
    } catch (err) {
      setActionMessage({ type: 'error', text: `Recovery failed: ${err.message}` });
    } finally {
      setRecoveryLoading(false);
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const handleCreateManualCheckpoint = async () => {
    try {
      const chk = await createCheckpoint(goalId, `Manual Operator Checkpoint`);
      setActionMessage({
        type: 'success',
        text: `State Checkpoint ${chk.checkpointId} created (${chk.fileCount} sandbox files captured).`,
      });
      await fetchIncidentsData();
    } catch (err) {
      setActionMessage({ type: 'error', text: `Failed to create checkpoint: ${err.message}` });
    } finally {
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const handleRollbackCheckpoint = async (chkId) => {
    const targetId = chkId || selectedCheckpointForRollback;
    if (!targetId) return;
    try {
      const res = await rollbackCheckpoint(targetId, goalId);
      setActionMessage({
        type: 'success',
        text: `Rollback completed: ${res.message} (${res.restoredFilesCount} files restored).`,
      });
      if (onUnfreezeSuccess) onUnfreezeSuccess();
      await fetchIncidentsData();
    } catch (err) {
      setActionMessage({ type: 'error', text: `Rollback failed: ${err.message}` });
    } finally {
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const handleVerifyAuditChain = async () => {
    setVerifyingAudit(true);
    try {
      const res = await verifyAuditChain(goalId);
      setAuditVerification(res);
      setActionMessage({
        type: res.isValid ? 'success' : 'error',
        text: res.summary,
      });
    } catch (err) {
      setActionMessage({ type: 'error', text: `Audit verification failed: ${err.message}` });
    } finally {
      setVerifyingAudit(false);
      setTimeout(() => setActionMessage(null), 5000);
    }
  };

  const handleCopyExplanation = () => {
    if (forensicExplanation?.formattedText) {
      navigator.clipboard.writeText(forensicExplanation.formattedText);
      setCopiedText(true);
      setTimeout(() => setCopiedText(false), 2000);
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

      {/* Top Banner: Metrics & Global Forensic Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4 rounded-2xl bg-gradient-to-br from-red-950/30 via-transparent to-transparent border border-red-500/30 shadow-lg relative overflow-hidden">
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

        <div className="card p-4 rounded-2xl bg-gradient-to-br from-cyan-950/30 via-transparent to-transparent border border-cyan-500/30 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
              <Play size={14} />
              Session Replay
            </span>
            <span className="text-[0.65rem] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 font-mono font-bold">
              TIMELINE
            </span>
          </div>
          <div className="mt-2">
            <button
              onClick={() => setReplayModalOpen(true)}
              className="w-full btn-primary py-2 px-3 text-xs font-bold flex items-center justify-center gap-1.5 shadow-md shadow-cyan-500/20"
              style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', border: 'none' }}
            >
              <Play size={13} />
              <span>Launch Session Replay</span>
            </button>
          </div>
        </div>

        <div className="card p-4 rounded-2xl bg-gradient-to-br from-indigo-950/30 via-transparent to-transparent border border-indigo-500/30 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
              <FileCheck size={14} />
              Audit Hash Chain
            </span>
            <button
              onClick={handleVerifyAuditChain}
              disabled={verifyingAudit}
              className="text-[0.65rem] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 font-mono font-bold hover:bg-indigo-500/30 flex items-center gap-1 transition-all"
            >
              <RefreshCw size={10} className={verifyingAudit ? 'animate-spin' : ''} />
              <span>Verify</span>
            </button>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs">
            <span className="text-[var(--color-text-muted)] text-[0.7rem]">
              {auditVerification ? (
                auditVerification.isValid ? (
                  <span className="text-emerald-400 font-bold flex items-center gap-1">
                    <CheckCircle2 size={12} /> {auditVerification.verifiedBlocks} Blocks Verified
                  </span>
                ) : (
                  <span className="text-red-400 font-bold flex items-center gap-1">
                    <AlertTriangle size={12} /> Tamper Detected
                  </span>
                )
              ) : (
                'SHA-256 Ledger Connected'
              )}
            </span>
            <button
              onClick={() => setCheckpointsOpen(!checkpointsOpen)}
              className="text-[0.7rem] text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1"
            >
              Checkpoints ({checkpoints.length})
            </button>
          </div>
        </div>
      </div>

      {/* Checkpoints Drawer (When Opened) */}
      {checkpointsOpen && (
        <div className="card p-4 rounded-2xl border border-indigo-500/40 bg-gradient-to-r from-indigo-950/30 via-[var(--color-bg-primary)] to-[var(--color-bg-secondary)] shadow-xl animate-fade-in space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <GitBranch size={16} className="text-indigo-400" />
              <h3 className="text-xs font-extrabold uppercase tracking-wider text-white">
                Sandbox Checkpoint &amp; Rollback Manager
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleCreateManualCheckpoint}
                className="btn-secondary py-1 px-2.5 text-xs font-bold text-cyan-400 border-cyan-500/40 hover:bg-cyan-500/10"
              >
                + Create Checkpoint
              </button>
              <button
                onClick={() => setCheckpointsOpen(false)}
                className="text-gray-400 hover:text-white text-xs"
              >
                Close
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 max-h-48 overflow-y-auto no-scrollbar">
            {checkpoints.length === 0 ? (
              <p className="text-xs text-[var(--color-text-muted)] py-4 text-center col-span-3">
                No checkpoints recorded yet. Automatic checkpoints are created before high-impact actions.
              </p>
            ) : (
              checkpoints.map((chk) => (
                <div
                  key={chk.checkpointId}
                  className="p-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-primary)] flex items-center justify-between text-xs"
                >
                  <div className="min-w-0">
                    <div className="font-mono text-cyan-400 font-bold truncate text-[0.7rem]">
                      {chk.checkpointId}
                    </div>
                    <div className="text-white font-medium truncate text-[0.7rem]">{chk.label}</div>
                    <div className="text-[0.6rem] text-[var(--color-text-muted)]">
                      {chk.fileCount} files &bull; {new Date(chk.createdAt).toLocaleTimeString()}
                    </div>
                  </div>
                  <button
                    onClick={() => handleRollbackCheckpoint(chk.checkpointId)}
                    className="btn-primary py-1 px-2 text-[0.65rem] font-bold bg-indigo-600 hover:bg-indigo-500 text-white shrink-0 ml-2"
                  >
                    Rollback
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

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

      {/* Main 2-Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 Cols) — Incident Feed */}
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
            <div className="space-y-2.5 max-h-[650px] overflow-y-auto pr-1 no-scrollbar">
              {filteredIncidents.length === 0 ? (
                <div className="text-center py-10 text-[var(--color-text-muted)] text-xs">
                  <CheckCircle2 size={32} className="mx-auto text-emerald-400 mb-2 opacity-80" />
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
                        <span className="text-cyan-400 font-bold flex items-center gap-0.5">
                          Inspect <ChevronRight size={10} />
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Column (7 Cols) — Deep Forensic Explanation, Blast Radius & 5-Option Recovery */}
        <div className="lg:col-span-7 space-y-4">
          {selectedIncident ? (
            <div className="card p-5 rounded-2xl border border-[var(--color-border)] shadow-xl space-y-5">
              {/* Incident Header */}
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
                    Containment State:{' '}
                    <span className="font-bold text-red-400 font-mono">
                      {selectedIncident.containmentAction || 'AGENT_FROZEN'}
                    </span>{' '}
                    &bull; Recorded at {new Date(selectedIncident.createdAt || Date.now()).toLocaleString()}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setReplayModalOpen(true)}
                    className="btn-secondary text-xs px-3 py-1.5 font-bold flex items-center gap-1 text-cyan-400 border-cyan-500/40 hover:bg-cyan-500/10"
                  >
                    <Play size={12} />
                    <span>Replay</span>
                  </button>
                  {selectedIncident.status === 'OPEN' && (
                    <button
                      onClick={() => handleResolve(selectedIncident.incidentId)}
                      className="btn-primary text-xs px-3 py-1.5 font-bold flex items-center gap-1 bg-emerald-600 hover:bg-emerald-500 text-white"
                    >
                      <Check size={12} />
                      <span>Resolve</span>
                    </button>
                  )}
                </div>
              </div>

              {/* 10-Point "WHY BLOCKED" Forensic Explanation Card */}
              {forensicExplanation && (
                <div className="p-4 rounded-2xl bg-gradient-to-br from-red-950/40 via-[var(--color-bg-primary)] to-[var(--color-bg-secondary)] border border-red-500/40 shadow-lg space-y-3">
                  <div className="flex items-center justify-between border-b border-red-500/20 pb-2">
                    <h4 className="text-xs font-extrabold uppercase tracking-wider text-red-300 flex items-center gap-1.5">
                      <ShieldAlert size={14} className="text-red-400" />
                      Forensic Explanation — WHY BLOCKED (10-Point Security Verdict)
                    </h4>
                    <button
                      onClick={handleCopyExplanation}
                      className="text-[0.65rem] font-bold text-gray-300 hover:text-white flex items-center gap-1 bg-white/5 px-2 py-0.5 rounded border border-white/10"
                    >
                      {copiedText ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                      <span>{copiedText ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[var(--color-text-muted)] text-[0.65rem] block font-bold">1. Original Goal</span>
                      <span className="text-white font-medium text-[0.75rem] truncate block">{forensicExplanation.originalGoal}</span>
                    </div>

                    <div>
                      <span className="text-[var(--color-text-muted)] text-[0.65rem] block font-bold">2. Current Action</span>
                      <span className="font-mono text-amber-300 text-[0.75rem] truncate block">{forensicExplanation.currentAction}</span>
                    </div>

                    <div>
                      <span className="text-[var(--color-text-muted)] text-[0.65rem] block font-bold">3. Source &amp; 5. Trust</span>
                      <span className="text-cyan-300 text-[0.75rem]">{forensicExplanation.source} ({forensicExplanation.trustLevel})</span>
                    </div>

                    <div>
                      <span className="text-[var(--color-text-muted)] text-[0.65rem] block font-bold">4. Goal Alignment</span>
                      <span className="text-red-400 font-mono font-bold text-[0.75rem]">{forensicExplanation.goalAlignment}</span>
                    </div>

                    <div>
                      <span className="text-[var(--color-text-muted)] text-[0.65rem] block font-bold">6. Risk Level</span>
                      <span className="text-red-400 font-bold text-[0.75rem]">{forensicExplanation.risk}</span>
                    </div>

                    <div>
                      <span className="text-[var(--color-text-muted)] text-[0.65rem] block font-bold">7. Trajectory</span>
                      <span className="text-amber-200 text-[0.75rem] truncate block">{forensicExplanation.trajectory}</span>
                    </div>

                    <div className="sm:col-span-2">
                      <span className="text-[var(--color-text-muted)] text-[0.65rem] block font-bold">8. Blast Radius Impact</span>
                      <span className="text-red-300 font-mono text-[0.7rem] block leading-relaxed">{forensicExplanation.blastRadius}</span>
                    </div>

                    <div>
                      <span className="text-[var(--color-text-muted)] text-[0.65rem] block font-bold">9. Gateway Decision</span>
                      <span className="px-2 py-0.5 rounded bg-red-500 text-black font-extrabold text-[0.65rem] inline-block">
                        {forensicExplanation.decision}
                      </span>
                    </div>

                    <div>
                      <span className="text-[var(--color-text-muted)] text-[0.65rem] block font-bold">10. Agent State</span>
                      <span className="text-red-400 font-mono font-bold text-[0.75rem]">{forensicExplanation.agentState}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* 5-Option Recovery Decision Control Bar */}
              <div className="p-4 rounded-2xl bg-[var(--color-bg-primary)] border border-cyan-500/30 space-y-3 shadow-lg">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-extrabold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                    <RotateCcw size={14} />
                    Autonomous Recovery Controls (5-Option Decision Engine)
                  </h4>
                  <span className="text-[0.6rem] font-mono text-gray-400">SELECT ACTION</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {/* Option 1: Continue */}
                  <button
                    onClick={() => handleExecuteRecovery('CONTINUE')}
                    disabled={recoveryLoading}
                    className="p-2.5 rounded-xl border border-emerald-500/40 bg-emerald-950/20 hover:bg-emerald-950/40 text-emerald-300 flex flex-col items-center justify-center gap-1 text-center transition-all"
                  >
                    <Unlock size={14} />
                    <span className="text-[0.65rem] font-bold">1. Continue</span>
                    <span className="text-[0.55rem] text-gray-400">Unfreeze Agent</span>
                  </button>

                  {/* Option 2: Abort */}
                  <button
                    onClick={() => handleExecuteRecovery('ABORT')}
                    disabled={recoveryLoading}
                    className="p-2.5 rounded-xl border border-red-500/40 bg-red-950/20 hover:bg-red-950/40 text-red-300 flex flex-col items-center justify-center gap-1 text-center transition-all"
                  >
                    <Ban size={14} />
                    <span className="text-[0.65rem] font-bold">2. Abort</span>
                    <span className="text-[0.55rem] text-gray-400">Terminate Session</span>
                  </button>

                  {/* Option 3: Rollback Checkpoint */}
                  <button
                    onClick={() => handleExecuteRecovery('ROLLBACK_CHECKPOINT')}
                    disabled={recoveryLoading || checkpoints.length === 0}
                    className="p-2.5 rounded-xl border border-indigo-500/40 bg-indigo-950/20 hover:bg-indigo-950/40 text-indigo-300 flex flex-col items-center justify-center gap-1 text-center transition-all disabled:opacity-40"
                  >
                    <RotateCcw size={14} />
                    <span className="text-[0.65rem] font-bold">3. Rollback</span>
                    <span className="text-[0.55rem] text-gray-400">Restore Sandbox</span>
                  </button>

                  {/* Option 4: Evolve Goal */}
                  <button
                    onClick={() => setEvolveModalOpen(true)}
                    disabled={recoveryLoading}
                    className="p-2.5 rounded-xl border border-cyan-500/40 bg-cyan-950/20 hover:bg-cyan-950/40 text-cyan-300 flex flex-col items-center justify-center gap-1 text-center transition-all"
                  >
                    <Sliders size={14} />
                    <span className="text-[0.65rem] font-bold">4. Evolve Goal</span>
                    <span className="text-[0.55rem] text-gray-400">Update Policy V2</span>
                  </button>

                  {/* Option 5: New Session */}
                  <button
                    onClick={() => handleExecuteRecovery('START_NEW_SESSION')}
                    disabled={recoveryLoading}
                    className="p-2.5 rounded-xl border border-gray-500/40 bg-gray-900/30 hover:bg-gray-900/50 text-gray-300 flex flex-col items-center justify-center gap-1 text-center transition-all"
                  >
                    <RefreshCw size={14} />
                    <span className="text-[0.65rem] font-bold">5. Reset</span>
                    <span className="text-[0.55rem] text-gray-400">New Session</span>
                  </button>
                </div>
              </div>

              {/* Multidimensional Blast Radius Surface Breakdown */}
              {selectedIncident.blastRadius && (
                <div className="p-4 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)] space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-extrabold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                      <Lock size={14} />
                      Multidimensional Blast Radius Assessment
                    </h4>
                    <span className="text-[0.65rem] font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-300 font-bold border border-red-500/40">
                      Level: {selectedIncident.blastRadius.blastRadiusLevel || 'CRITICAL'} ({selectedIncident.blastRadius.blastRadiusScore || 85}%)
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)]">
                      <span className="text-[0.65rem] text-[var(--color-text-muted)] font-bold block">Files Targeted</span>
                      <span className="font-mono text-amber-300 text-[0.7rem] truncate block mt-0.5">
                        {selectedIncident.blastRadius.filesAffected?.length > 0
                          ? selectedIncident.blastRadius.filesAffected.join(', ')
                          : 'None'}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)]">
                      <span className="text-[0.65rem] text-[var(--color-text-muted)] font-bold block">Database Objects</span>
                      <span className="font-mono text-cyan-300 text-[0.7rem] truncate block mt-0.5">
                        {selectedIncident.blastRadius.databaseObjectsAffected?.length > 0
                          ? selectedIncident.blastRadius.databaseObjectsAffected.join(', ')
                          : 'None'}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)]">
                      <span className="text-[0.65rem] text-[var(--color-text-muted)] font-bold block">Network Endpoints</span>
                      <span className="font-mono text-emerald-300 text-[0.7rem] truncate block mt-0.5">
                        {selectedIncident.blastRadius.networkDestinations?.length > 0
                          ? selectedIncident.blastRadius.networkDestinations.join(', ')
                          : 'None'}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)]">
                      <span className="text-[0.65rem] text-[var(--color-text-muted)] font-bold block">Privileges Required</span>
                      <span className="font-mono text-red-300 text-[0.7rem] truncate block mt-0.5">
                        {selectedIncident.blastRadius.privilegesRequired || 'STANDARD_USER'}
                      </span>
                    </div>
                  </div>

                  <p className="text-[0.7rem] text-[var(--color-text-muted)] leading-relaxed">
                    {selectedIncident.blastRadius.summary}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="card p-12 rounded-2xl border border-[var(--color-border)] shadow-xl text-center space-y-3">
              <CheckCircle2 size={48} className="mx-auto text-cyan-400 opacity-80" />
              <h3 className="text-base font-extrabold text-white">No Incident Selected</h3>
              <p className="text-xs text-[var(--color-text-muted)] max-w-sm mx-auto">
                Select an incident from the security feed on the left to inspect its 10-point explanation, blast radius, and recovery options.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Evolve Goal Modal Dialog */}
      {evolveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
          <div className="card w-full max-w-lg p-5 rounded-2xl border border-cyan-500/40 bg-[var(--color-bg-secondary)] shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-3">
              <h3 className="text-sm font-extrabold text-white flex items-center gap-2">
                <Sliders size={16} className="text-cyan-400" />
                Evolve Goal &amp; Expand Policy (V2)
              </h3>
              <button onClick={() => setEvolveModalOpen(false)} className="text-gray-400 hover:text-white">
                <XCircle size={16} />
              </button>
            </div>

            <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
              If the blocked action was legitimately intended, update the goal statement or add explicit scope permissions.
            </p>

            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-300">Evolved Goal Objective:</label>
              <textarea
                value={evolveGoalText}
                onChange={(e) => setEvolveGoalText(e.target.value)}
                placeholder="e.g. Build React application with backend server routes..."
                rows={3}
                className="w-full p-2.5 rounded-xl bg-[var(--color-bg-primary)] border border-[var(--color-border)] text-xs text-white focus:border-cyan-500 outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setEvolveModalOpen(false)}
                className="btn-secondary py-1.5 px-3 text-xs font-bold text-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={() => handleExecuteRecovery('EVOLVE_GOAL', { evolvedGoal: evolveGoalText })}
                disabled={!evolveGoalText.trim() || recoveryLoading}
                className="btn-primary py-1.5 px-4 text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white"
              >
                Apply Evolved Goal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Session Replay Modal */}
      <SessionReplayModal
        isOpen={replayModalOpen}
        onClose={() => setReplayModalOpen(false)}
        goalId={goalId}
      />
    </div>
  );
}
