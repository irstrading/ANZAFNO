import React from 'react';
import { useScannerStore, ScannerItem } from '../../store/scannerStore';
import { ArrowUp, ArrowDown, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

const ScannerTable: React.FC = () => {
  const { items, loading } = useScannerStore();

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'LONG_BUILDUP': return 'text-bull bg-bull/10 border-bull/20';
      case 'SHORT_COVERING': return 'text-bull bg-bull/5 border-bull/10';
      case 'SHORT_BUILDUP': return 'text-bear bg-bear/10 border-bear/20';
      case 'LONG_UNWINDING': return 'text-bear bg-bear/5 border-bear/10';
      default: return 'text-text-muted bg-surface border-border';
    }
  };

  if (loading) return <div className="p-8 text-center text-text-muted">Loading scanner data...</div>;

  return (
    <div className="overflow-x-auto rounded-xl border border-border bg-surface">
      <table className="w-full text-left text-sm">
        <thead className="bg-secondary/50 text-text-muted font-medium border-b border-border">
          <tr>
            <th className="px-6 py-4">SYMBOL</th>
            <th className="px-6 py-4 text-right">PRICE</th>
            <th className="px-6 py-4 text-center">CHANGE %</th>
            <th className="px-6 py-4 text-center">OI SIGNAL</th>
            <th className="px-6 py-4 text-center">PCR</th>
            <th className="px-6 py-4 text-right">MAX PAIN</th>
            <th className="px-6 py-4 text-center">SCORE</th>
            <th className="px-6 py-4 text-right">ACTION</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {items.map((item) => (
            <tr key={item.symbol} className="hover:bg-secondary/30 transition-colors">
              <td className="px-6 py-4 font-bold text-primary">{item.symbol}</td>

              <td className="px-6 py-4 text-right font-mono">
                {item.ltp.toLocaleString('en-IN')}
              </td>

              <td className={`px-6 py-4 text-center font-bold ${item.change >= 0 ? 'text-bull' : 'text-bear'}`}>
                <div className="flex items-center justify-center gap-1">
                  {item.change >= 0 ? <ArrowUp size={14} /> : <ArrowDown size={14} />}
                  {Math.abs(item.change)}%
                </div>
              </td>

              <td className="px-6 py-4 text-center">
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getSignalColor(item.oi_signal)}`}>
                  {item.oi_signal.replace('_', ' ')}
                </span>
              </td>

              <td className="px-6 py-4 text-center font-mono">
                <span className={item.pcr > 1.2 ? 'text-bull' : item.pcr < 0.7 ? 'text-bear' : 'text-text-muted'}>
                  {item.pcr}
                </span>
              </td>

              <td className="px-6 py-4 text-right font-mono text-text-muted">
                {item.max_pain}
              </td>

              <td className="px-6 py-4 text-center">
                <div className="relative w-12 h-12 mx-auto flex items-center justify-center">
                  <svg className="absolute w-full h-full transform -rotate-90">
                    <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4" fill="none" className="text-border" />
                    <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4" fill="none"
                      strokeDasharray="126"
                      strokeDashoffset={126 - (126 * item.score) / 100}
                      className={item.score > 70 ? 'text-bull' : item.score < 40 ? 'text-bear' : 'text-neutral'}
                    />
                  </svg>
                  <span className="text-xs font-bold">{item.score}</span>
                </div>
              </td>

              <td className="px-6 py-4 text-right">
                <Link
                  to={`/analysis/${item.symbol}`}
                  className="p-2 inline-flex rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                >
                  <ExternalLink size={16} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ScannerTable;
