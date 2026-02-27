import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const GreeksChart: React.FC = () => {
  const data = [
    { strike: 21400, gex: -120000 },
    { strike: 21500, gex: -80000 },
    { strike: 21600, gex: 50000 }, // Flip level
    { strike: 21700, gex: 150000 },
    { strike: 21800, gex: 200000 },
  ];

  return (
    <div className="h-full w-full bg-surface rounded-xl border border-border p-4">
      <h3 className="text-text-muted text-xs font-bold mb-4 uppercase tracking-wider">Gamma Exposure (GEX)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorGex" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0}/>
            </linearGradient>
          </defs>
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
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <Tooltip
             contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', color: 'var(--color-text)' }}
          />
          <Area
            type="monotone"
            dataKey="gex"
            stroke="var(--color-primary)"
            fillOpacity={1}
            fill="url(#colorGex)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default GreeksChart;
