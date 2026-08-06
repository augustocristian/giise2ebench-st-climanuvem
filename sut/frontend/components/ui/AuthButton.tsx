import React from 'react';
import { TouchableOpacity, Text, ActivityIndicator, ViewStyle, TextStyle } from 'react-native';
import { useTheme } from '@/src/contexts/ThemeContext';
import { getAuthButtonStyles } from '@/src/styles/globalStyles';
import { Ionicons } from '@expo/vector-icons';

interface AuthButtonProps {
  title: string;
  onPress: () => void;
  loading?: boolean;
  variant?: 'primary' | 'secondary' | 'google' | 'outline';
  icon?: keyof typeof Ionicons.glyphMap;
  style?: ViewStyle;
  textStyle?: TextStyle;
  disabled?: boolean;
}

export const AuthButton = ({ 
  title, 
  onPress, 
  loading, 
  variant = 'primary', 
  icon, 
  style, 
  textStyle,
  disabled 
}: AuthButtonProps) => {
  const { theme } = useTheme();
  const styles = getAuthButtonStyles(theme);

  const isGoogle = variant === 'google';
  const isOutline = variant === 'outline';

  const getIconColor = () => {
    if (isGoogle) return '#db4437';
    if (isOutline) return theme.colors.primary;
    return 'white';
  };

  return (
    <TouchableOpacity 
      style={[
        styles.button, 
        styles[variant], 
        (loading || disabled) && styles.disabled, 
        style
      ]} 
      onPress={onPress}
      accessibilityRole="button"
      disabled={loading || disabled}
    >
      {loading ? (
        <ActivityIndicator color={isGoogle || isOutline ? theme.colors.primary : 'white'} />
      ) : (
        <>
          {icon && (
            <Ionicons 
              name={icon} 
              size={20} 
              color={getIconColor()} 
              style={styles.icon} 
            />
          )}
          <Text style={[
            styles.text, 
            isGoogle && styles.googleText, 
            isOutline && styles.outlineText,
            textStyle
          ]}>
            {title}
          </Text>
        </>
      )}
    </TouchableOpacity>
  );
};

