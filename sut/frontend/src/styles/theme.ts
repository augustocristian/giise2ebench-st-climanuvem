export interface Theme {
  mode: 'light' | 'dark';
  colors: {
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    primary: string;
    danger: string;
    border: string;
    success: string;
    overlay: string;
    tagBackground: string;
    warning: string;
  };
}

export const lightTheme: Theme = {
  mode: 'light',
  colors: {
    background: '#FFFFFF',
    surface: '#F5F5F5',
    text: '#1A1A1A',
    textSecondary: '#666666',
    primary: '#007AFF',
    danger: '#F44336',
    border: '#E0E0E0',
    success: '#4CAF50',
    overlay: 'rgba(0,0,0,0.5)',
    tagBackground: '#E8E8E8',
    warning: '#FF9800',
  },
};

export const darkTheme: Theme = {
  mode: 'dark',
  colors: {
    background: '#121212',
    surface: '#1E1E1E',
    text: '#E0E0E0',
    textSecondary: '#A0A0A0',
    primary: '#64B5F6',
    danger: '#EF5350',
    border: '#333333',
    success: '#81C784',
    overlay: 'rgba(0,0,0,0.7)',
    tagBackground: '#2C2C2C',
    warning: '#FFB74D',
  },
};
