import React from 'react';
import { useParams } from 'react-router-dom';
import OptionChainTable from '../components/analysis/OptionChainTable';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const StockAnalysis: React.FC = () => {
  const { symbol } = useParams();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/" className="p-2 rounded-lg bg-surface hover:bg-border transition-colors text-text-muted">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-text flex items-center gap-2">
            {symbol} <span className="text-sm font-normal text-text-muted bg-surface px-2 py-0.5 rounded border border-border">NSE</span>
          </h1>
          <div className="flex items-center gap-4 text-sm mt-1">
            <span className="text-bull font-bold">₹2,845.00 (+1.2%)</span>
            <span className="text-text-muted">VWAP: 2842.50</span>
            <span className="text-text-muted">OI: 4.2M (+12%)</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart Area */}
        <div className="lg:col-span-2 h-[400px] bg-surface rounded-xl border border-border flex items-center justify-center text-text-muted">
          [ TradingView / Recharts Candle Chart Placeholder ]
        </div>

        {/* Stats Panel */}
        <div className="space-y-4">
          <div className="p-4 bg-surface rounded-xl border border-border">
            <h3 className="text-sm font-bold text-text-muted mb-4">GREEK EXPOSURE</h3>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>Delta</span>
                <span className="text-bull">+450K</span>
              </div>
              <div className="w-full bg-secondary h-1.5 rounded-full overflow-hidden">
                <div className="bg-bull w-3/4 h-full" />
              </div>

              <div className="flex justify-between text-sm mt-2">
                <span>Gamma</span>
                <span className="text-bear">-120K</span>
              </div>
              <div className="w-full bg-secondary h-1.5 rounded-full overflow-hidden">
                <div className="bg-bear w-1/4 h-full" />
              </div>
            </div>
          </div>

          <div className="p-4 bg-surface rounded-xl border border-border">
            <h3 className="text-sm font-bold text-text-muted mb-2">KEY LEVELS</h3>
            <div className="flex justify-between py-2 border-b border-border/50">
              <span>Max Pain</span>
              <span className="font-mono font-bold text-neutral">21,600</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border/50">
              <span>Call Wall</span>
              <span className="font-mono font-bold text-bear">21,800</span>
            </div>
            <div className="flex justify-between py-2">
              <span>Put Wall</span>
              <span className="font-mono font-bold text-bull">21,400</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-bold text-text mb-4">Option Chain</h2>
        <OptionChainTable />
      </div>
    </div>
  );
};

export default StockAnalysis;
