import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  BarChart2,
  Search,
  Activity,
  List,
  AlertTriangle,
  Settings
} from 'lucide-react';

const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 h-screen bg-surface border-r border-border flex flex-col p-4 fixed left-0 top-0">
      <div className="flex items-center gap-3 mb-8 px-2">
        <div className="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center text-primary font-bold text-xl">
          A
        </div>
        <div className="flex flex-col">
            <span className="font-bold text-lg tracking-wide text-text">ANZA FNO</span>
            <span className="text-xs text-text-muted">Intelligence</span>
        </div>
      </div>

      <nav className="flex-1 space-y-2">
        <NavLink
          to="/"
          className={({ isActive }) => `
            flex items-center gap-3 px-4 py-3 rounded-xl transition-all
            ${isActive
              ? 'bg-primary/10 text-primary font-medium'
              : 'text-text-muted hover:bg-white/5 hover:text-text'}
          `}
        >
          <Search size={20} />
          Scanner
        </NavLink>

        <NavLink
          to="/nifty-desk"
          className={({ isActive }) => `
            flex items-center gap-3 px-4 py-3 rounded-xl transition-all
            ${isActive ? 'bg-primary/10 text-primary' : 'text-text-muted hover:bg-white/5'}
          `}
        >
          <Activity size={20} />
          Nifty Desk
        </NavLink>

        <NavLink
          to="/watchlist"
          className={({ isActive }) => `
            flex items-center gap-3 px-4 py-3 rounded-xl transition-all
            ${isActive ? 'bg-primary/10 text-primary' : 'text-text-muted hover:bg-white/5'}
          `}
        >
          <List size={20} />
          Watchlist
        </NavLink>

        <NavLink
          to="/analysis"
          className={({ isActive }) => `
            flex items-center gap-3 px-4 py-3 rounded-xl transition-all
            ${isActive ? 'bg-primary/10 text-primary' : 'text-text-muted hover:bg-white/5'}
          `}
        >
          <BarChart2 size={20} />
          Analysis
        </NavLink>

        <NavLink
          to="/alerts"
          className={({ isActive }) => `
            flex items-center gap-3 px-4 py-3 rounded-xl transition-all
            ${isActive ? 'bg-primary/10 text-primary' : 'text-text-muted hover:bg-white/5'}
          `}
        >
          <AlertTriangle size={20} />
          Alerts
        </NavLink>
      </nav>

      <div className="mt-auto border-t border-border pt-4">
        <NavLink
          to="/settings"
          className={({ isActive }) => `
            flex items-center gap-3 px-4 py-3 rounded-xl transition-all
            ${isActive ? 'bg-primary/10 text-primary' : 'text-text-muted hover:bg-white/5'}
          `}
        >
          <Settings size={20} />
          Settings
        </NavLink>
      </div>
    </aside>
  );
};

export default Sidebar;
