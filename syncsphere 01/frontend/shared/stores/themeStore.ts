import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type AppTheme = 'light' | 'dark' | 'cyberpunk' | 'forest' | 'slate';

interface ThemeState {
  theme: AppTheme;
  setTheme: (theme: AppTheme) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'dark', // Default to Dark mode
      setTheme: (theme) => {
        if (typeof window !== 'undefined') {
          const root = window.document.documentElement;
          // Remove existing theme classes
          root.classList.remove('light', 'dark', 'theme-cyberpunk', 'theme-forest', 'theme-slate');
          // Add appropriate theme class
          if (theme === 'light') {
            root.classList.add('light');
            root.style.colorScheme = 'light';
          } else if (theme === 'dark') {
            root.classList.add('dark');
            root.style.colorScheme = 'dark';
          } else {
            root.classList.add('dark', `theme-${theme}`);
            root.style.colorScheme = 'dark';
          }
        }
        set({ theme });
      },
    }),
    {
      name: 'syncsphere-theme',
    }
  )
);
