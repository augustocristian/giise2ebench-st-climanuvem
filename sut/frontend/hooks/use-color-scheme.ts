import { useTheme } from '@/src/contexts/ThemeContext';

export function useColorScheme() {
  const { theme } = useTheme();
  return theme.mode;
}
