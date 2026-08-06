/**
 * Learn more about light and dark modes:
 * https://docs.expo.dev/guides/color-schemes/
 */

import { useTheme } from '@/src/contexts/ThemeContext';

export function useThemeColor(
  props: { light?: string; dark?: string },
  colorName: string
) {
  const { theme } = useTheme();
  const colorFromProps = props[theme.mode];

  if (colorFromProps) {
    return colorFromProps;
  } else {
    // @ts-ignore - We know colorName is a valid key for theme.colors in our usage
    return theme.colors[colorName] || theme.colors.text;
  }
}
