import React from 'react';
import { useParams } from 'react-router-dom';

export interface OptionChainRow {
  strike: number;
  ce_oi: number;
  ce_change: number;
  ce_ltp: number;
  pe_oi: number;
  pe_change: number;
  pe_ltp: number;
  max_pain?: boolean;
}

// Dummy data generator
const generateChain = (atm: number): OptionChainRow[] => {
  const strikes = [];
  for (let i = -5; i <= 5; i++) {
    strikes.push({
      strike: atm + i * 100,
      ce_oi: Math.floor(Math.random() * 50000),
      ce_change: Math.floor(Math.random() * 10000) - 5000,
      ce_ltp: Math.abs(200 - i * 20),
      pe_oi: Math.floor(Math.random() * 50000),
      pe_change: Math.floor(Math.random() * 10000) - 5000,
      pe_ltp: Math.abs(100 + i * 20),
      max_pain: i === 0
    });
  }
  return strikes;
};

const OptionChainTable: React.FC = () => {
  const { symbol } = useParams();
  const data = generateChain(21500); // Mock data for now

  return (
    <div className="overflow-x-auto rounded-xl border border-border bg-surface">
      <table className="w-full text-xs font-mono">
        <thead className="bg-secondary/50 text-text-muted font-bold border-b border-border">
          <tr>
            <th colSpan={4} className="py-2 text-center border-r border-border text-bull">CALLS (CE)</th>
            <th className="py-2 text-center w-24 bg-surface text-text font-black text-sm">STRIKE</th>
            <th colSpan={4} className="py-2 text-center border-l border-border text-bear">PUTS (PE)</th>
          </tr>
          <tr className="border-b border-border/50 text-[10px] tracking-wider">
            <th className="py-2 w-16">OI</th>
            <th className="py-2 w-16">CHG</th>
            <th className="py-2 w-12">VOL</th>
            <th className="py-2 w-16 border-r border-border">LTP</th>

            <th className="bg-surface"></th>

            <th className="py-2 w-16 border-l border-border">LTP</th>
            <th className="py-2 w-12">VOL</th>
            <th className="py-2 w-16">CHG</th>
            <th className="py-2 w-16">OI</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/20">
          {data.map((row) => (
            <tr key={row.strike} className={`hover:bg-secondary/20 transition-colors ${row.max_pain ? 'bg-neutral/5' : ''}`}>
              {/* CE Side */}
              <td className="py-1 px-2 text-right text-text relative">
                <div className="absolute top-1 bottom-1 left-0 bg-bull/10 z-0" style={{ width: `${(row.ce_oi/50000)*100}%` }} />
                <span className="relative z-10">{row.ce_oi.toLocaleString()}</span>
              </td>
              <td className={`py-1 px-2 text-right ${row.ce_change >= 0 ? 'text-bull' : 'text-bear'}`}>
                {row.ce_change}
              </td>
              <td className="py-1 px-2 text-right text-text-muted">1.2K</td>
              <td className="py-1 px-2 text-right text-primary border-r border-border font-bold">
                {row.ce_ltp.toFixed(1)}
              </td>

              {/* Strike */}
              <td className={`py-2 px-2 text-center font-bold bg-surface border-x border-border
                ${row.max_pain ? 'text-neutral bg-neutral/10' : 'text-text'}
              `}>
                {row.strike}
                {row.max_pain && <span className="ml-1 text-[8px] text-neutral bg-neutral/20 px-1 rounded">MP</span>}
              </td>

              {/* PE Side */}
              <td className="py-1 px-2 text-left text-primary border-l border-border font-bold">
                {row.pe_ltp.toFixed(1)}
              </td>
              <td className="py-1 px-2 text-left text-text-muted">800</td>
              <td className={`py-1 px-2 text-left ${row.pe_change >= 0 ? 'text-bull' : 'text-bear'}`}>
                {row.pe_change}
              </td>
              <td className="py-1 px-2 text-left text-text relative">
                <div className="absolute top-1 bottom-1 right-0 bg-bear/10 z-0" style={{ width: `${(row.pe_oi/50000)*100}%` }} />
                <span className="relative z-10">{row.pe_oi.toLocaleString()}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default OptionChainTable;
