import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpBackend from 'i18next-http-backend';

// Load local JSON resources directly for initial languages (en, es)
// We also keep HttpBackend enabled so we can lazy load future languages/files
import en from './locales/en/translation.json';
import es from './locales/es/translation.json';

const resources = {
  en: { translation: en },
  es: { translation: es },
};

const detectionOptions = {
  // order and from where user language should be detected
  order: ['localStorage', 'navigator', 'htmlTag', 'cookie', 'path', 'subdomain'],
  // keys or params to lookup language from
  lookupLocalStorage: 'i18nextLng',
  caches: ['localStorage', 'cookie'],
};

i18next
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: false,
    detection: detectionOptions,
    interpolation: {
      escapeValue: false, // React already escapes by default
    },
    // If using backend to load, specify load path; we still bundle local files for en/es
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },
    react: {
      useSuspense: false,
    },
    returnObjects: true,
  });

// Keep <html lang> in sync for accessibility/SEO
const setHtmlLang = (lng) => {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = lng || 'en';
    document.documentElement.dir = 'ltr'; // prep for future RTL support
  }
};

setHtmlLang(i18next.resolvedLanguage);

i18next.on('languageChanged', (lng) => setHtmlLang(lng));

export default i18next;
