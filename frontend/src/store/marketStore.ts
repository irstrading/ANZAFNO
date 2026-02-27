import { create } from 'zustand';
import api from '../lib/axios';

interface MarketData {
    nifty: { ltp: number; change: number; pcr: number } | null;
    banknifty: { ltp: number; change: number; pcr: number } | null;
    timestamp: string | null;
    loading: boolean;
    error: string | null;
}

interface MarketStore extends MarketData {
    fetchMarketOverview: () => Promise<void>;
}

export const useMarketStore = create<MarketStore>((set) => ({
    nifty: null,
    banknifty: null,
    timestamp: null,
    loading: false,
    error: null,
    fetchMarketOverview: async () => {
        set({ loading: true });
        try {
            const res = await api.get('/scanner/overview');
            set({
                nifty: res.data.nifty,
                banknifty: res.data.banknifty,
                timestamp: res.data.timestamp,
                loading: false
            });
        } catch (err: any) {
            set({ error: err.message, loading: false });
        }
    }
}));
