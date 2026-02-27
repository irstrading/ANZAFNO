import React, { useState } from 'react';
import Scanner from './pages/Scanner';
import NiftyDesk from './pages/NiftyDesk';
import Watchlist from './pages/Watchlist';
export default function App() {
  const [page, setPage] = useState('scanner');
  return (
    <div className="min-h-screen bg-[#040508] text-[#c8d8f0]">
      <header className="border-b border-white/5 p-4 flex justify-between bg-[#070b12]">
        <h1 className="text-xl font-bold">ANZA <span className="text-[#00c8ff]">FNO</span></h1>
        <nav className="flex gap-4">
          <button onClick={() => setPage('scanner')}>Scanner</button>
          <button onClick={() => setPage('nifty')}>NiftyDesk</button>
          <button onClick={() => setPage('watchlist')}>Watchlist</button>
        </nav>
      </header>
      <main className="p-6">
        {page === 'scanner' && <Scanner />}
        {page === 'nifty' && <NiftyDesk />}
        {page === 'watchlist' && <Watchlist />}
      </main>
    </div>
  );
}
