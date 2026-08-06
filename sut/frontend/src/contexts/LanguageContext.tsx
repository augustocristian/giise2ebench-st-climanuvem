import React, { createContext, useContext, useEffect, useMemo, useCallback } from 'react';
import * as Localization from 'expo-localization';
import i18n from '../i18n';
import { usePersistedPreference } from '@/src/hooks/usePersistedPreference';

export type LanguageMode = 'en' | 'es' | 'system';

interface LanguageContextType {
  languageMode: LanguageMode;
  setLanguageMode: (mode: LanguageMode) => void;
}

const LanguageContext = createContext<LanguageContextType>({
  languageMode: 'system',
  setLanguageMode: () => {},
});

const getConfiguredLanguage = () => {
  const configuredLanguage = process.env.EXPO_PUBLIC_DEFAULT_LANGUAGE;
  return configuredLanguage === 'es' || configuredLanguage === 'en'
    ? configuredLanguage
    : undefined;
};

export const useLanguage = () => useContext(LanguageContext);

const isLanguageMode = (value: string): value is LanguageMode =>
  value === 'en' || value === 'es' || value === 'system';

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [languageModeState, setStoredLanguageMode] = usePersistedPreference<LanguageMode>('appLanguage', 'system', isLanguageMode);

  const applyLanguage = useCallback((mode: LanguageMode) => {
    const configuredLanguage = getConfiguredLanguage();
    if (configuredLanguage) {
      i18n.changeLanguage(configuredLanguage);
      return;
    }

    let lngToSet = mode;
    if (mode === 'system') {
      const locales = Localization.getLocales();
      if (locales && locales.length > 0) {
        const sysLng = locales[0].languageCode;
        lngToSet = (sysLng === 'es' || sysLng === 'en') ? sysLng : 'en';
      } else {
        lngToSet = 'en';
      }
    }
    i18n.changeLanguage(lngToSet);
  }, []);

  const setLanguageMode = useCallback(async (mode: LanguageMode) => {
    applyLanguage(mode);
    await setStoredLanguageMode(mode);
  }, [applyLanguage, setStoredLanguageMode]);

  useEffect(() => {
    applyLanguage(languageModeState);
  }, [applyLanguage, languageModeState]);

  const contextValue = useMemo(() => ({
    languageMode: languageModeState,
    setLanguageMode
  }), [languageModeState, setLanguageMode]);

  return (
    <LanguageContext.Provider value={contextValue}>
      {children}
    </LanguageContext.Provider>
  );
};
