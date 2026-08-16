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
      <div className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] p-2.5 sm:p-3 rounded-lg shadow-xl text-xs space-y-1 z-50 max-w-xs">
        <div className="font-bold text-[var(--color-text-primary)] border-b border-[var(--color-border)] pb-1 mb-1 truncate">
          Action #{label}: {data.actionType} {data.target ? `(${data.target})` : ''}
        </div>
        <div className="text-cyan-400 font-semibold text-[0.7rem] sm:text-xs">
          Rolling Goal Integrity: {data.rollingIntegrity}%
        </div>
        <div className="text-emerald-400 text-[0.7rem] sm:text-xs">
          Action Alignment: {data.alignmentScore}%
        </div>
        <div className="text-red-400 text-[0.7rem] sm:text-xs">
          Cumulative Risk: {data.cumulativeRiskScore}%
        </div>
        <div className="text-[var(--color-text-muted)] text-[0.6rem] sm:text-[0.65rem] pt-0.5">
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
      <div className="glass-card p-4 sm:p-6 mb-6">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp size={18} className="text-cyan-400 shrink-0" />
          <h3 className="text-xs sm:text-sm font-bold tracking-wide uppercase text-[var(--color-text-primary)] truncate">
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
    <div className="glass-card p-4 sm:p-6 mb-6 animate-fade-in-up border border-[var(--color-border)]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-4 pb-3 border-b border-[var(--color-border)]">
        <div className="flex items-start sm:items-center gap-2.5 min-w-0">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isDeclining ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'}`}>
            {isDeclining ? <AlertTriangle size={17} /> : <ShieldCheck size={17} />}
          </div>
          <div className="min-w-0">
            <h3 className="text-xs sm:text-sm font-bold tracking-wide uppercase text-[var(--color-text-primary)] truncate">
              Goal Integrity Over Agent Execution
            </h3>
            <p className="text-[0.65rem] sm:text-[0.7rem] text-[var(--color-text-muted)] leading-normal">
              Continuous multi-step trajectory monitoring comparing agent actions against original goal policy
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
          <div className="text-right">
            <span className="text-[0.6rem] sm:text-[0.65rem] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold block">
              Current Rolling Integrity
            </span>
            <span className={`text-sm sm:text-base font-bold font-mono ${latestIntegrity >= 80 ? 'text-cyan-400' : latestIntegrity >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
              {latestIntegrity}%
            </span>
          </div>
        </div>
      </div>

      {/* Recharts Line Chart */}
      <div className="w-full h-56 sm:h-64 mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
            <XAxis
              dataKey="actionIndex"
              stroke="#94a3b8"
              fontSize={10}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#94a3b8"
              fontSize={10}
              tickLine={false}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '0.65rem', paddingTop: '8px' }}
              iconType="circle"
            />
            <ReferenceLine
              y={50}
              stroke="#f59e0b"
              strokeDasharray="4 4"
              label={{ value: 'Drift (50%)', fill: '#f59e0b', fontSize: 9, position: 'insideBottomRight' }}
            />
            <Line
              type="monotone"
              dataKey="rollingIntegrity"
              name="Rolling Integrity"
              stroke="#06b6d4"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#06b6d4', stroke: '#0e7490', strokeWidth: 1.5 }}
              activeDot={{ r: 5, fill: '#38bdf8' }}
            />
            <Line
              type="monotone"
              dataKey="alignmentScore"
              name="Alignment"
              stroke="#10b981"
              strokeWidth={1.5}
              strokeDasharray="2 2"
              dot={{ r: 2.5, fill: '#10b981' }}
            />
            <Line
              type="monotone"
              dataKey="cumulativeRiskScore"
              name="Risk"
              stroke="#ef4444"
              strokeWidth={1.5}
              dot={{ r: 2.5, fill: '#ef4444' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
