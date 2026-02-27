import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const OIChart: React.FC = () => {
  const data = [
    { strike: 21400, ce_oi: 20000, pe_oi: 50000 },
    { strike: 21500, ce_oi: 35000, pe_oi: 45000 },
    { strike: 21600, ce_oi: 60000, pe_oi: 30000 },
    { strike: 21700, ce_oi: 80000, pe_oi: 15000 },
    { strike: 21800, ce_oi: 90000, pe_oi: 5000 },
  ];

  return (
    <div className="h-full w-full bg-surface rounded-xl border border-border p-4">
      <h3 className="text-text-muted text-xs font-bold mb-4 uppercase tracking-wider">Open Interest Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="strike"
            tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }}
            itemStyle={{ color: 'var(--color-text)' }}
            cursor={{ fill: 'var(--color-secondary)' }}
          />
          <Legend />
          <Bar dataKey="ce_oi" name="Call OI" fill="var(--color-bear)" radius={[4, 4, 0, 0]} />
          <Bar dataKey="pe_oi" name="Put OI" fill="var(--color-bull)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default OIChart;
