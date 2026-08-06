import React from 'react';
import { View, TextInput, TouchableOpacity, TextInputProps } from 'react-native';
import { useTheme } from '@/src/contexts/ThemeContext';
import { getAuthInputStyles } from '@/src/styles/globalStyles';
import { Ionicons } from '@expo/vector-icons';

interface AuthInputProps extends TextInputProps {
  icon?: keyof typeof Ionicons.glyphMap;
  showEyeIcon?: boolean;
  onEyePress?: () => void;
  secureTextEntry?: boolean;
}

export const AuthInput = React.forwardRef<TextInput, AuthInputProps>(
  ({ icon, showEyeIcon, onEyePress, secureTextEntry, style, ...props }, ref) => {
    const { theme } = useTheme();
    const styles = getAuthInputStyles(theme);

    return (
      <View style={styles.container}>
        {icon && <Ionicons name={icon} size={20} color={theme.colors.textSecondary} style={styles.icon} />}
        <TextInput
          ref={ref}
          style={[styles.input, style]}
          placeholderTextColor={theme.colors.textSecondary}
          secureTextEntry={secureTextEntry}
          {...props}
        />
        {showEyeIcon && (
          <TouchableOpacity onPress={onEyePress} style={styles.eyeIcon}>
            <Ionicons name={secureTextEntry ? 'eye' : 'eye-off'} size={24} color={theme.colors.textSecondary} />
          </TouchableOpacity>
        )}
      </View>
    );
  }
);

AuthInput.displayName = 'AuthInput';


