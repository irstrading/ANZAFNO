import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './components/layout/DashboardLayout';
import Scanner from './pages/Scanner';
import StockAnalysis from './pages/StockAnalysis';
import { useThemeStore } from './store/themeStore';

const App: React.FC = () => {
  const { theme } = useThemeStore();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Scanner />} />
          <Route path="analysis/:symbol" element={<StockAnalysis />} />

          {/* Placeholders for future routes */}
          <Route path="nifty-desk" element={<div className="p-8 text-text-muted">Nifty Desk Coming Soon</div>} />
          <Route path="watchlist" element={<div className="p-8 text-text-muted">Watchlist Coming Soon</div>} />
          <Route path="analysis" element={<Navigate to="/" replace />} />
          <Route path="alerts" element={<div className="p-8 text-text-muted">Alerts Coming Soon</div>} />
          <Route path="settings" element={<div className="p-8 text-text-muted">Settings Coming Soon</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
