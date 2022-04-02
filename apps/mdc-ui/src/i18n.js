import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import backend from 'i18next-http-backend';

i18n
  .use(initReactI18next) // passes i18n down to react-i18next
  .use(backend)
  .init({
    fallbackLng: 'en',
    lng: 'en',
    keySeparator: false,
    backend: {
      loadPath: `${process.env.PUBLIC_URL}/locales/{{lng}}/{{ns}}.json`,
    },
  });

export default i18n;
