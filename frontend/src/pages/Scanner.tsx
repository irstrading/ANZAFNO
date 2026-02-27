import React from 'react';
import ScannerTable from '../components/scanner/ScannerTable';
import { Filter, RefreshCcw } from 'lucide-react';

const Scanner: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text mb-1">Market Scanner</h1>
          <p className="text-text-muted text-sm">Real-time momentum & OI analysis</p>
        </div>

        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface border border-border hover:bg-secondary transition-colors text-sm">
            <Filter size={16} />
            Filters
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 text-white transition-colors text-sm font-medium">
            <RefreshCcw size={16} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-surface border border-border">
          <div className="text-text-muted text-xs font-bold mb-1">TOTAL SCANNED</div>
          <div className="text-2xl font-bold text-text">184</div>
        </div>
        <div className="p-4 rounded-xl bg-surface border border-border">
          <div className="text-bull text-xs font-bold mb-1">BULLISH SETUPS</div>
          <div className="text-2xl font-bold text-bull">12</div>
        </div>
        <div className="p-4 rounded-xl bg-surface border border-border">
          <div className="text-bear text-xs font-bold mb-1">BEARISH SETUPS</div>
          <div className="text-2xl font-bold text-bear">8</div>
        </div>
        <div className="p-4 rounded-xl bg-surface border border-border">
          <div className="text-neutral text-xs font-bold mb-1">NEUTRAL / CHOPPY</div>
          <div className="text-2xl font-bold text-neutral">164</div>
        </div>
      </div>

      <ScannerTable />
    </div>
  );
};

export default Scanner;
