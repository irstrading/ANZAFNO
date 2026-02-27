import React from 'react';
import { ThemeSwitcher } from './ThemeSwitcher';
import { useMarketStore } from '../../store/marketStore';

const Header: React.FC = () => {
    // In real app, these would come from store
    const nifty = { price: 21500, change: 120, pct: 0.56 };
    const banknifty = { price: 47800, change: -150, pct: -0.32 };
    const vix = 14.5;

    return (
        <header className="h-16 bg-surface border-b border-border flex items-center justify-between px-6 fixed top-0 left-64 right-0 z-10">
            {/* Market Ticker */}
            <div className="flex items-center gap-8 text-sm font-medium">
                <div className="flex items-center gap-2">
                    <span className="text-text-muted">NIFTY</span>
                    <span className={nifty.change >= 0 ? 'text-bull' : 'text-bear'}>
                        {nifty.price.toLocaleString()}
                        <span className="text-xs ml-1">({nifty.pct}%)</span>
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-text-muted">BANKNIFTY</span>
                    <span className={banknifty.change >= 0 ? 'text-bull' : 'text-bear'}>
                        {banknifty.price.toLocaleString()}
                        <span className="text-xs ml-1">({banknifty.pct}%)</span>
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-text-muted">INDIA VIX</span>
                    <span className={vix > 20 ? 'text-bear' : 'text-neutral'}>
                        {vix}
                    </span>
                </div>
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-4">
                <div className="px-3 py-1 rounded-full bg-bull/10 text-bull text-xs font-bold border border-bull/20">
                    MARKET OPEN
                </div>
                <ThemeSwitcher />
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs font-bold">
                    IA
                </div>
            </div>
        </header>
    );
};

export default Header;
