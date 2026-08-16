import { useState, useEffect, useCallback } from 'react';
import GoalSetup from './pages/GoalSetup';
import Dashboard from './pages/Dashboard';
import { createGoal, startAgent, startScenarioDemo, startOpenAIDemo, getActiveSession } from './services/api';
import { usePolling } from './hooks/usePolling';

/**
 * App — Root component with Automatic Antigravity Auto-Sync.
 * Automatically switches to Dashboard as soon as Antigravity registers a goal via PreInvocation/PreToolUse!
 */
export default function App() {
  const [currentGoalId, setCurrentGoalId] = useState(null);

  // Poll for active Antigravity session
  const { data: sessionStatus } = usePolling(
    useCallback(() => getActiveSession(), []),
    600,
    true
  );

  // Auto-switch to Dashboard & follow active Antigravity goal in real-time
  useEffect(() => {
    if (sessionStatus?.connected && sessionStatus?.activeGoalId) {
      if (currentGoalId !== sessionStatus.activeGoalId) {
        setCurrentGoalId(sessionStatus.activeGoalId);
      }
    }
  }, [sessionStatus?.activeGoalId, sessionStatus?.connected, currentGoalId]);

  const handleStart = async (userGoal, constraints, isDemo = false, scenarioId = null, goalPolicy = null, monitorMode = false) => {
    if (scenarioId) {
      const res = await startScenarioDemo(scenarioId);
      setCurrentGoalId(res.goalId);
    } else if (isDemo) {
      const res = await startOpenAIDemo();
      setCurrentGoalId(res.goalId);
    } else {
      // 1. Create goal in MongoDB
      const { goalId } = await createGoal(userGoal, constraints, goalPolicy);
      // 2. Switch to dashboard
      setCurrentGoalId(goalId);
      // 3. Only start OpenAI Agent if not in Antigravity monitor mode
      if (!monitorMode) {
        await startAgent(goalId);
      }
    }
  };

  const handleReset = () => {
    setCurrentGoalId(null);
  };

  if (currentGoalId) {
    return (
      <Dashboard
        goalId={currentGoalId}
        onReset={handleReset}
        sessionStatus={sessionStatus}
      />
    );
  }

  return (
    <GoalSetup
      onStart={handleStart}
      sessionStatus={sessionStatus}
    />
  );
}


