import { create } from 'zustand';

// Dummy scanner data for now, replace with API call later
export interface ScannerItem {
    symbol: string;
    ltp: number;
    change: number;
    oi_signal: string; // "LONG_BUILDUP", etc.
    pcr: number;
    max_pain: number;
    score: number;
}

interface ScannerStore {
    items: ScannerItem[];
    loading: boolean;
    fetchScanner: () => Promise<void>;
}

export const useScannerStore = create<ScannerStore>((set) => ({
    items: [
        { symbol: "RELIANCE", ltp: 2850, change: 1.2, oi_signal: "LONG_BUILDUP", pcr: 1.1, max_pain: 2840, score: 85 },
        { symbol: "TATASTEEL", ltp: 145, change: -0.5, oi_signal: "SHORT_BUILDUP", pcr: 0.6, max_pain: 148, score: 30 },
        { symbol: "INFY", ltp: 1620, change: 0.8, oi_signal: "SHORT_COVERING", pcr: 0.9, max_pain: 1600, score: 65 },
    ],
    loading: false,
    fetchScanner: async () => {
        // Placeholder for API call
        // const res = await api.get('/scanner/top');
        // set({ items: res.data });
    }
}));
