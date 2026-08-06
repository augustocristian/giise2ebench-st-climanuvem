import i18n from '@/src/i18n';

export const EMAIL_REGEX = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

/**
 * Translates Firebase error codes into friendly, internationalized messages.
 */
export function getAuthErrorMessage(errorCode: string): string {
  const key = errorCode.split('/')[1];
  
  if (key && i18n.exists(`authErrors.${key}`)) {
    return i18n.t(`authErrors.${key}`);
  }
  
  return `${i18n.t('authErrors.default')}: ${errorCode}`;
}

