import React, { createContext, useContext, useMemo } from 'react';
import { useColorScheme } from 'react-native';
import { Theme, lightTheme, darkTheme } from '../styles/theme';
import { usePersistedPreference } from '@/src/hooks/usePersistedPreference';

export type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: lightTheme,
  themeMode: 'system',
  setThemeMode: () => {},
});

export const useTheme = () => useContext(ThemeContext);

const isThemeMode = (value: string): value is ThemeMode =>
  value === 'light' || value === 'dark' || value === 'system';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const systemColorScheme = useColorScheme();
  const [themeModeState, setThemeMode] = usePersistedPreference<ThemeMode>('appTheme', 'system', isThemeMode);

  const currentThemeMode = themeModeState === 'system' ? (systemColorScheme || 'light') : themeModeState;
  const theme = currentThemeMode === 'dark' ? darkTheme : lightTheme;

  const contextValue = useMemo(() => ({
    theme,
    themeMode: themeModeState,
    setThemeMode
  }), [theme, themeModeState, setThemeMode]);

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};
