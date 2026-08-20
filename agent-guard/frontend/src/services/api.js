/**
 * API Service — Axios wrapper for all Agent Guard backend endpoints.
 */

import axios from 'axios';

const getApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (typeof window !== 'undefined') {
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    // If running in production on Vercel / non-localhost and envUrl is localhost or empty, route to Render backend
    if (!isLocalhost && (!envUrl || envUrl.includes('localhost') || envUrl.includes('127.0.0.1'))) {
      return 'https://safe-guard-backend-5hra.onrender.com';
    }
  }
  return envUrl || 'http://localhost:8000';
};

const API_BASE = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Goal Endpoints ────────────────────────────────────────────

export async function analyzeGoal(userGoal, constraints = []) {
  const res = await api.post('/api/goals/analyze', { userGoal, constraints });
  return res.data;
}

export async function createGoal(userGoal, constraints = [], goalPolicy = null) {
  const res = await api.post('/api/goals', { userGoal, constraints, goalPolicy });
  return res.data;
}

export async function getGoal(goalId) {
  const res = await api.get(`/api/goals/${goalId}`);
  return res.data;
}

export async function startAgent(goalId) {
  const res = await api.post(`/api/goals/${goalId}/start`);
  return res.data;
}

export async function getActions(goalId) {
  const res = await api.get(`/api/goals/${goalId}/actions`);
  return res.data;
}

export async function getDashboard(goalId) {
  const res = await api.get(`/api/goals/${goalId}/dashboard`);
  return res.data;
}

export async function resetGoal(goalId) {
  const res = await api.post(`/api/goals/${goalId}/reset`);
  return res.data;
}

export async function startScenarioDemo(scenarioId = 'scenario-1') {
  const res = await api.post(`/api/demo/scenario/${scenarioId}`);
  return res.data;
}

export async function startOpenAIDemo() {
  const res = await api.post('/api/demo/openai');
  return res.data;
}

export async function modifyGoal(goalId, userGoal, constraints = [], changeReason = 'User updated goal scope') {
  const res = await api.post(`/api/goals/${goalId}/modify`, { userGoal, constraints, changeReason });
  return res.data;
}

export async function resumeAgent(goalId) {
  const res = await api.post(`/api/goals/${goalId}/resume`);
  return res.data;
}

export async function getGoalHistory(goalId) {
  const res = await api.get(`/api/goals/${goalId}/history`);
  return res.data;
}

export async function stopAgent(goalId) {
  const res = await api.post(`/api/goals/${goalId}/stop`);
  return res.data;
}

export async function approveAction(actionId, approvalMode = "ONCE", reason = "User approved via dashboard") {
  const res = await api.post(`/api/actions/${actionId}/approve`, { approvalMode, reason });
  return res.data;
}

export async function rejectAction(actionId, reason = "User rejected via dashboard") {
  const res = await api.post(`/api/actions/${actionId}/reject`, { reason });
  return res.data;
}

export async function abortGoal(goalId) {
  const res = await api.post(`/api/goals/${goalId}/abort`);
  return res.data;
}

export async function getGoalIntent(goalId) {
  const res = await api.get(`/api/goals/${goalId}/intent`);
  return res.data;
}

export async function getGoalSubGoals(goalId) {
  const res = await api.get(`/api/goals/${goalId}/sub-goal`);
  return res.data;
}

export async function evaluateContextInstruction(content, source = "WEBSITE", goalId = null) {
  const res = await api.post('/api/context/evaluate-instruction', { content, source, goalId });
  return res.data;
}

export async function runRealWorldBookingSimulation() {
  const res = await api.post('/api/demo/real-world-booking');
  return res.data;
}

// ─── Antigravity Agent Endpoints ───────────────────────────────

export async function getAgentStatus() {
  const res = await api.get('/api/agent/status');
  return res.data;
}

export async function getActiveSession() {
  const res = await api.get('/api/agent/session/active');
  return res.data;
}

export async function bindSession(conversationId, goalId, agent = 'antigravity') {
  const res = await api.post('/api/agent/session/bind', { conversationId, goalId, agent });
  return res.data;
}

export async function connectAgent(sessionId = null, conversationId = null) {
  const res = await api.post('/api/agent/connect', { sessionId, conversationId });
  return res.data;
}

export async function disconnectAgent(sessionId = null, conversationId = null) {
  const res = await api.post('/api/agent/disconnect', { sessionId, conversationId });
  return res.data;
}

// ─── Advanced Feature Endpoints ────────────────────────────────

export async function simulateThreat(goalId, attackType, customPrompt = null, customTarget = null) {
  const res = await api.post('/api/threats/simulate', { goalId, attackType, customPrompt, customTarget });
  return res.data;
}

export async function evaluatePolicyAction(goalId, actionType, target, description) {
  const res = await api.post('/api/policy/evaluate', { goalId, actionType, target, description });
  return res.data;
}

export async function getComplianceReport(goalId) {
  const res = await api.get(`/api/compliance/report/${goalId}`);
  return res.data;
}

// ─── Phase 3 & 4: Incident, Forensics & Recovery Endpoints ─────

export async function getIncidents(goalId) {
  const res = await api.get(`/api/incidents/${goalId}`);
  return res.data;
}

export async function getIncidentSummary(goalId) {
  const res = await api.get(`/api/incidents/${goalId}/summary`);
  return res.data;
}

export async function getIncidentDetail(incidentId) {
  const res = await api.get(`/api/incidents/detail/${incidentId}`);
  return res.data;
}

export async function getForensicExplanation(incidentId) {
  const res = await api.get(`/api/incidents/${incidentId}/explanation`);
  return res.data;
}

export async function resolveIncident(incidentId) {
  const res = await api.post(`/api/incidents/${incidentId}/resolve`);
  return res.data;
}

export async function recoverIncident(incidentId, action, params = {}) {
  const res = await api.post(`/api/incidents/${incidentId}/recover`, {
    action,
    ...params,
  });
  return res.data;
}

export async function unfreezeGoalAfterIncident(goalId) {
  const res = await api.post(`/api/incidents/${goalId}/unfreeze`);
  return res.data;
}

// ─── Phase 4: Checkpoints, Blast Radius & Audit Verification ───

export async function createCheckpoint(goalId, label = 'Manual Checkpoint', metadata = {}) {
  const res = await api.post('/api/checkpoints', { goalId, label, metadata });
  return res.data;
}

export async function getCheckpoints(goalId) {
  const res = await api.get(`/api/checkpoints/${goalId}`);
  return res.data;
}

export async function rollbackCheckpoint(checkpointId, goalId) {
  const res = await api.post(`/api/checkpoints/${checkpointId}/rollback?goal_id=${goalId}`);
  return res.data;
}

export async function verifyAuditChain(goalId = null) {
  const endpoint = goalId ? `/api/audit/verify/${goalId}` : '/api/audit/verify';
  const res = await api.get(endpoint);
  return res.data;
}

export async function getAuditLogs(goalId) {
  const res = await api.get(`/api/audit/${goalId}`);
  return res.data;
}

export async function getSessionReplay(goalId) {
  const res = await api.get(`/api/goals/${goalId}/replay`);
  return res.data;
}

export default api;




