// frontend/src/pages/Scanner.jsx
import React from 'react';
export default function Scanner() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-4">
        <div className="anza-card p-4">Market Regime: NEG GEX</div>
        <div className="anza-card p-4">Nifty: 23,450</div>
      </div>
      <div className="anza-card p-4">Live Scanner Table</div>
    </div>
  );
}
