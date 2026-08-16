import { useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';

/**
 * ThemeToggle — Modern dark & light mode switcher.
 * Persists theme in localStorage and toggles the [data-theme] attribute on <html>.
 */
export default function ThemeToggle({ className = '' }) {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('agent_guard_theme') || 'dark';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'light') {
      root.setAttribute('data-theme', 'light');
      root.classList.add('light');
      root.classList.remove('dark');
    } else {
      root.setAttribute('data-theme', 'dark');
      root.classList.add('dark');
      root.classList.remove('light');
    }
    localStorage.setItem('agent_guard_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const isLight = theme === 'light';

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`p-2 rounded-full border border-[var(--color-border)] bg-[var(--color-bg-primary)] hover:border-cyan-500/50 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-all duration-200 shadow-sm flex items-center justify-center ${className}`}
      title={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
      aria-label="Toggle theme"
    >
      {isLight ? (
        <Moon size={16} className="text-indigo-600 transition-transform duration-300 hover:rotate-12" />
      ) : (
        <Sun size={16} className="text-amber-400 transition-transform duration-300 hover:rotate-45" />
      )}
    </button>
  );
}
