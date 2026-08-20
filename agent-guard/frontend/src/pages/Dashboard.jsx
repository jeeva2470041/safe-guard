import { useState, useCallback } from 'react';
import Header from '../components/Header';
import GoalCard from '../components/GoalCard';
import GoalIntegrityCard from '../components/GoalIntegrityCard';
import StatsCards from '../components/StatsCards';
import ActivityTimeline from '../components/ActivityTimeline';
import ActionDetailModal from '../components/ActionDetailModal';
import CompletionScreen from '../components/CompletionScreen';
import EnforcementProofPanel from '../components/EnforcementProofPanel';
import GoalIntegrityTrendChart from '../components/GoalIntegrityTrendChart';
import AgentPausedInterventionModal from '../components/AgentPausedInterventionModal';
import AgentBehaviorSummary from '../components/AgentBehaviorSummary';
import GoalVersionHistory from '../components/GoalVersionHistory';
import ConnectedAgentCard from '../components/ConnectedAgentCard';
import ConnectIdeModal from '../components/ConnectIdeModal';
import ThreatSimulator from '../components/ThreatSimulator';
import PolicySandbox from '../components/PolicySandbox';
import ComplianceAudit from '../components/ComplianceAudit';
import IncidentForensics from '../components/IncidentForensics';
import { usePolling } from '../hooks/usePolling';
import {
  getGoal,
  getActions,
  getDashboard,
  getAgentStatus,
  getIncidentSummary,
  approveAction,
  rejectAction,
  abortGoal,
  resetGoal,
  resumeAgent,
  stopAgent,
  modifyGoal,
} from '../services/api';

/**
 * Dashboard — Full-Spectrum AI Security Operations Center dashboard.
 * Supports live SOC monitoring, Red Team Threat Simulator, Policy Sandbox, and Compliance Audit.
 */
export default function Dashboard({ goalId, onReset, sessionStatus, onStatusChange }) {
  const [selectedAction, setSelectedAction] = useState(null);
  const [connectModalOpen, setConnectModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Poll agent status specifically for dashboard
  const { data: liveAgentStatus } = usePolling(
    useCallback(() => getAgentStatus(), []),
    1500,
    true
  );

  const effectiveStatus = liveAgentStatus || sessionStatus;

  // Poll goal data
  const { data: goal } = usePolling(
    useCallback(() => getGoal(goalId), [goalId]),
    600,
    !!goalId
  );

  // Poll actions
  const { data: actions } = usePolling(
    useCallback(() => getActions(goalId), [goalId]),
    600,
    !!goalId
  );

  // Poll dashboard stats
  const { data: dashboard } = usePolling(
    useCallback(() => getDashboard(goalId), [goalId]),
    600,
    !!goalId
  );

  // Poll incident summary stats (Phase 3)
  const { data: incidentSummary } = usePolling(
    useCallback(() => getIncidentSummary(goalId), [goalId]),
    1000,
    !!goalId
  );

  const agentStatus = goal?.status || 'IDLE';
  const isCompleted = agentStatus === 'COMPLETED';
  const isPaused = agentStatus === 'PAUSED' || Boolean(dashboard?.pauseReason);

  const handleApprove = async (actionId, approvalMode = 'ONCE') => {
    try {
      await approveAction(actionId, approvalMode);
      setSelectedAction(null);
    } catch (err) {
      console.error('Failed to approve:', err);
    }
  };

  const handleReject = async (actionId) => {
    try {
      await rejectAction(actionId);
      setSelectedAction(null);
    } catch (err) {
      console.error('Failed to reject:', err);
    }
  };

  const handleAbort = async (targetGoalId) => {
    try {
      await abortGoal(targetGoalId || goalId);
      setSelectedAction(null);
    } catch (err) {
      console.error('Failed to abort:', err);
    }
  };

  const handleResume = async () => {
    try {
      await resumeAgent(goalId);
    } catch (err) {
      console.error('Failed to resume:', err);
    }
  };

  const handleStop = async () => {
    try {
      await stopAgent(goalId);
    } catch (err) {
      console.error('Failed to stop:', err);
    }
  };

  const handleModifyGoal = async (newGoal, newConstraints, changeReason) => {
    try {
      await modifyGoal(goalId, newGoal, newConstraints, changeReason);
    } catch (err) {
      console.error('Failed to modify goal:', err);
    }
  };

  const handleReset = async () => {
    try {
      await resetGoal(goalId);
      onReset();
    } catch (err) {
      console.error('Failed to reset:', err);
    }
  };

  const scrollToTimeline = () => {
    setActiveTab('dashboard');
    setTimeout(() => {
      const el = document.getElementById('activity-timeline-section');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        agentStatus={agentStatus}
        onReset={handleReset}
        sessionStatus={effectiveStatus}
        onOpenConnectModal={() => setConnectModalOpen(true)}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        showNav={true}
        openIncidentsCount={incidentSummary?.open || 0}
      />

      <main className="flex-1 max-w-[1440px] mx-auto w-full px-6 py-6">
        <div key={activeTab} className="animate-tab-pane space-y-6">
          {/* Tab: Attack Forensics View (Phase 3) */}
          {activeTab === 'incidents' && (
            <IncidentForensics
              goalId={goalId}
              onUnfreezeSuccess={handleResume}
              onModifyGoalRequest={() => {}}
            />
          )}

          {/* Tab 1: Threat Simulator View */}
          {activeTab === 'threats' && (
            <ThreatSimulator goalId={goalId} />
          )}

          {/* Tab 2: Policy Sandbox View */}
          {activeTab === 'sandbox' && (
            <PolicySandbox goalId={goalId} />
          )}

          {/* Tab 3: Compliance & Audit View */}
          {activeTab === 'compliance' && (
            <ComplianceAudit goalId={goalId} />
          )}

          {/* Tab 0: Core Live SOC Dashboard View */}
          {activeTab === 'dashboard' && (
            <>
              {/* Enforcement & Security Proof Panel */}
              <EnforcementProofPanel actions={actions || []} />

              {/* Automatic Security Intervention Banner when Paused */}
              {isPaused && (
                <AgentPausedInterventionModal
                  goalId={goalId}
                  originalGoal={goal?.userGoal}
                  originalConstraints={goal?.constraints || []}
                  goalVersion={goal?.goalVersion || dashboard?.goalVersion || 1}
                  pauseReason={goal?.pauseReason || dashboard?.pauseReason}
                  recentDivergentAction={goal?.recentDivergentAction || dashboard?.recentDivergentAction}
                  overallGoalIntegrity={dashboard?.overallGoalIntegrity ?? dashboard?.goalIntegrityScore ?? 0}
                  cumulativeRiskLevel={dashboard?.cumulativeRiskLevel || 'CRITICAL'}
                  cumulativeRiskScore={dashboard?.cumulativeRiskScore || 85}
                  onResume={handleResume}
                  onStop={handleStop}
                  onModifyGoal={handleModifyGoal}
                />
              )}

              {/* Completion Screen when goal is done and not paused */}
              {isCompleted && !isPaused && (
                <CompletionScreen
                  goal={goal}
                  dashboard={dashboard}
                  onReset={handleReset}
                />
              )}

              {/* Goal Integrity Trend Chart (Recharts continuous visualization) */}
              <GoalIntegrityTrendChart trendData={dashboard?.trendData || []} />

              {/* Main Dashboard 2-Column Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Column — Connected Agent Card, Goal Policy & Telemetry Cards */}
                <div className="lg:col-span-4 space-y-5">
                  <ConnectedAgentCard
                    status={effectiveStatus}
                    onOpenConnectModal={() => setConnectModalOpen(true)}
                    onViewActivity={scrollToTimeline}
                    onStatusChange={onStatusChange}
                  />
                  <GoalCard goal={goal} />
                  <StatsCards dashboard={dashboard} />
                  <GoalIntegrityCard
                    actions={actions || []}
                    score={dashboard?.overallGoalIntegrity ?? dashboard?.goalIntegrityScore ?? 100}
                  />
                  <GoalVersionHistory
                    goalVersion={goal?.goalVersion || dashboard?.goalVersion || 1}
                    versionHistory={goal?.versionHistory || []}
                  />
                </div>

                {/* Right Column — Live Activity Timeline & Behavior Summary */}
                <div id="activity-timeline-section" className="lg:col-span-8 space-y-5">
                  <ActivityTimeline
                    actions={actions || []}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    onSelectAction={setSelectedAction}
                  />

                  {/* Agent Behavior & Security Telemetry Summary */}
                  <AgentBehaviorSummary summary={dashboard?.behaviorSummary || {}} />
                </div>
              </div>
            </>
          )}
        </div>
      </main>

      {/* Action Detail Modal */}
      <ActionDetailModal
        action={selectedAction}
        onClose={() => setSelectedAction(null)}
        onApprove={handleApprove}
        onReject={handleReject}
        onAbort={handleAbort}
      />

      {/* Connect IDE Modal */}
      <ConnectIdeModal
        isOpen={connectModalOpen}
        onClose={() => setConnectModalOpen(false)}
        initialStatus={effectiveStatus}
        onStatusChange={onStatusChange}
      />
    </div>
  );
}
