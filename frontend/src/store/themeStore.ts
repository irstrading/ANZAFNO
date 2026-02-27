import { create } from 'zustand';

export type Theme =
  | 'dark-terminal'
  | 'neon-quantum'
  | 'velonic-steel'
  | 'upcube-admin'
  | 'light-professional'
  | 'crypto-dark';

interface ThemeState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: 'dark-terminal', // Default
  setTheme: (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    set({ theme });
  },
}));
