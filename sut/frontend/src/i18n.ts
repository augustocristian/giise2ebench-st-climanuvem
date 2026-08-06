import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as Localization from 'expo-localization';

import en from './config/locales/en';
import es from './config/locales/es';

const resources = {
  en,
  es,
};

// Obtenemos el idioma del sistema
const getSystemLocale = () => {
  const configuredLanguage = process.env.EXPO_PUBLIC_DEFAULT_LANGUAGE;
  if (configuredLanguage === 'es' || configuredLanguage === 'en') {
    return configuredLanguage;
  }

  const locales = Localization.getLocales();
  if (locales && locales.length > 0) {
    const languageCode = locales[0].languageCode;
    // Solo soportamos en y es, si es otro usamos en por defecto
    if (languageCode === 'es' || languageCode === 'en') {
      return languageCode;
    }
  }
  return 'en';
};

// @ts-ignore: TS sugiere usar el export nombrado, pero necesitamos la instancia principal
i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: getSystemLocale(), // Idioma inicial
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // react already safes from xss
    },
    compatibilityJSON: 'v4', // Required for React Native
  });

export default i18n;
