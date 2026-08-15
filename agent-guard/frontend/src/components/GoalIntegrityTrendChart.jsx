import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, AlertTriangle, ShieldCheck } from 'lucide-react';

/**
 * Custom Tooltip for Goal Integrity Trend Chart.
 */
function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] p-3 rounded-lg shadow-xl text-xs space-y-1 z-50">
        <div className="font-bold text-[var(--color-text-primary)] border-b border-[var(--color-border)] pb-1 mb-1">
          Action #{label}: {data.actionType} {data.target ? `(${data.target})` : ''}
        </div>
        <div className="text-cyan-400 font-semibold">
          Rolling Goal Integrity: {data.rollingIntegrity}%
        </div>
        <div className="text-emerald-400">
          Action Alignment: {data.alignmentScore}%
        </div>
        <div className="text-red-400">
          Cumulative Risk: {data.cumulativeRiskScore}%
        </div>
        <div className="text-[var(--color-text-muted)] text-[0.65rem] pt-1">
          Decision: <span className="font-mono font-bold text-white">{data.decision}</span>
        </div>
      </div>
    );
  }
  return null;
}

/**
 * GoalIntegrityTrendChart — Visualizes continuous goal integrity trajectory over execution.
 */
export default function GoalIntegrityTrendChart({ trendData = [] }) {
  if (!trendData || trendData.length === 0) {
    return (
      <div className="glass-card p-6 mb-6">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp size={18} className="text-cyan-400" />
          <h3 className="text-sm font-bold tracking-wide uppercase text-[var(--color-text-primary)]">
            Goal Integrity Over Agent Execution
          </h3>
        </div>
        <p className="text-xs text-[var(--color-text-muted)] italic">
          Waiting for agent actions to plot goal integrity trajectory...
        </p>
      </div>
    );
  }

  // Format data for chart
  const formattedData = trendData.map((d, index) => ({
    ...d,
    actionIndex: `A${d.actionNumber || index + 1}`,
  }));

  const latestIntegrity = trendData[trendData.length - 1]?.rollingIntegrity ?? 100;
  const isDeclining = latestIntegrity < 70;

  return (
    <div className="glass-card p-6 mb-6 animate-fade-in-up border border-[var(--color-border)]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2.5">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isDeclining ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'}`}>
            {isDeclining ? <AlertTriangle size={18} /> : <ShieldCheck size={18} />}
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-wide uppercase text-[var(--color-text-primary)]">
              Goal Integrity Over Agent Execution
            </h3>
            <p className="text-[0.7rem] text-[var(--color-text-muted)]">
              Continuous multi-step trajectory monitoring comparing agent actions against original goal policy
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-center">
          <div className="text-right">
            <span className="text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold block">
              Current Rolling Integrity
            </span>
            <span className={`text-base font-bold font-mono ${latestIntegrity >= 80 ? 'text-cyan-400' : latestIntegrity >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
              {latestIntegrity}%
            </span>
          </div>
        </div>
      </div>

      {/* Recharts Line Chart */}
      <div className="w-full h-64 mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
            <XAxis
              dataKey="actionIndex"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '0.75rem', paddingTop: '10px' }}
              iconType="circle"
            />
            <ReferenceLine
              y={50}
              stroke="#f59e0b"
              strokeDasharray="4 4"
              label={{ value: 'Drift Threshold (50%)', fill: '#f59e0b', fontSize: 10, position: 'insideBottomRight' }}
            />
            <Line
              type="monotone"
              dataKey="rollingIntegrity"
              name="Rolling Goal Integrity"
              stroke="#06b6d4"
              strokeWidth={3}
              dot={{ r: 4, fill: '#06b6d4', stroke: '#0e7490', strokeWidth: 2 }}
              activeDot={{ r: 6, fill: '#38bdf8' }}
            />
            <Line
              type="monotone"
              dataKey="alignmentScore"
              name="Action Alignment"
              stroke="#10b981"
              strokeWidth={1.5}
              strokeDasharray="2 2"
              dot={{ r: 3, fill: '#10b981' }}
            />
            <Line
              type="monotone"
              dataKey="cumulativeRiskScore"
              name="Cumulative Risk"
              stroke="#ef4444"
              strokeWidth={2}
              dot={{ r: 3, fill: '#ef4444' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
