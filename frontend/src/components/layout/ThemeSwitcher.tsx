import React from 'react';
import { useThemeStore, Theme } from '../../store/themeStore';
import { Palette } from 'lucide-react';

const themes: { id: Theme; name: string }[] = [
    { id: 'dark-terminal', name: 'Dark Terminal' },
    { id: 'neon-quantum', name: 'Neon Quantum' },
    { id: 'velonic-steel', name: 'Velonic Steel' },
    { id: 'upcube-admin', name: 'Upcube Admin' },
    { id: 'light-professional', name: 'Light Pro' },
    { id: 'crypto-dark', name: 'Crypto Dark' },
];

export const ThemeSwitcher: React.FC = () => {
    const { theme, setTheme } = useThemeStore();
    const [isOpen, setIsOpen] = React.useState(false);

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-2 rounded-lg bg-surface hover:bg-border transition-colors text-text"
                title="Change Theme"
            >
                <Palette size={20} />
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-surface border border-border rounded-lg shadow-xl z-50">
                    {themes.map((t) => (
                        <button
                            key={t.id}
                            onClick={() => { setTheme(t.id); setIsOpen(false); }}
                            className={`w-full text-left px-4 py-2 text-sm hover:bg-border transition-colors
                                ${theme === t.id ? 'text-primary font-bold' : 'text-text-muted'}
                            `}
                        >
                            {t.name}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};
