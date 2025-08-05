import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from 'react';
import { ThemeConfig } from '@/types';

interface ThemeContextType {
  theme: ThemeConfig;
  updateTheme: (updates: Partial<ThemeConfig>) => void;
  toggleMode: () => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const defaultTheme: ThemeConfig = {
  mode: 'system',
  primaryColor: '#3b82f6',
  accentColor: '#d946ef',
  fontSize: 'md',
  animations: true,
};

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setTheme] = useState<ThemeConfig>(defaultTheme);
  const [isDark, setIsDark] = useState(false);

  // Initialize theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('quote_master_theme');
    if (savedTheme) {
      try {
        const parsed = JSON.parse(savedTheme);
        setTheme({ ...defaultTheme, ...parsed });
      } catch (error) {
        console.error('Failed to parse saved theme:', error);
      }
    }
  }, []);

  // Apply theme changes
  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem('quote_master_theme', JSON.stringify(theme));
  }, [theme]);

  // Handle system theme changes
  useEffect(() => {
    if (theme.mode === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = (e: MediaQueryListEvent) => {
        setIsDark(e.matches);
        updateDocumentClass(e.matches);
      };

      setIsDark(mediaQuery.matches);
      updateDocumentClass(mediaQuery.matches);
      mediaQuery.addEventListener('change', handleChange);

      return () => mediaQuery.removeEventListener('change', handleChange);
    } else {
      const dark = theme.mode === 'dark';
      setIsDark(dark);
      updateDocumentClass(dark);
    }
  }, [theme.mode]);

  const applyTheme = (themeConfig: ThemeConfig) => {
    const root = document.documentElement;

    // Apply CSS custom properties
    root.style.setProperty('--color-primary', themeConfig.primaryColor);
    root.style.setProperty('--color-accent', themeConfig.accentColor);

    // Apply font size
    const fontSizeMap = {
      sm: '14px',
      md: '16px',
      lg: '18px',
    };
    root.style.setProperty('--font-size-base', fontSizeMap[themeConfig.fontSize]);

    // Apply animations
    if (!themeConfig.animations) {
      root.style.setProperty('--animation-duration', '0ms');
      root.style.setProperty('--transition-duration', '0ms');
    } else {
      root.style.setProperty('--animation-duration', '300ms');
      root.style.setProperty('--transition-duration', '150ms');
    }
  };

  const updateDocumentClass = (dark: boolean) => {
    if (dark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const updateTheme = (updates: Partial<ThemeConfig>) => {
    setTheme(prev => ({ ...prev, ...updates }));
  };

  const toggleMode = () => {
    setTheme(prev => ({
      ...prev,
      mode: prev.mode === 'dark' ? 'light' : 'dark',
    }));
  };

  const value = {
    theme,
    updateTheme,
    toggleMode,
    isDark,
  };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

export { ThemeContext };