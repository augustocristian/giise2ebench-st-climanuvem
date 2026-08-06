import { Theme } from '@/src/styles/theme';

export const getStatusColor = (status: string, theme: Theme) => {
  switch (status) {
    case 'completed':
      return theme.colors.success;
    case 'analyzing':
      return theme.colors.primary;
    case 'cancelled':
      return theme.colors.danger;
    default:
      return theme.colors.textSecondary;
  }
};

export const getStatusText = (status: string) => {
  if (!status) return '';
  return status.charAt(0).toUpperCase() + status.slice(1);
};

export const getWarningLevelColor = (level: number, theme: Theme) => {
  switch (level) {
    case 0:
      return theme.colors.textSecondary;
    case 1:
      return theme.colors.warning;
    case 2:
      return theme.colors.danger;
    case 3:
      return theme.mode === 'dark' ? '#FF8A80' : '#B71C1C';
    default:
      return theme.colors.danger;
  }
};

export const formatDate = (dateString: string, language: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString(language === 'es' ? 'es-ES' : 'en-US', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};
