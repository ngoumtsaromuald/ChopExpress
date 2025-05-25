import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

// Import des traductions
import frTranslations from './locales/fr.json';
import enTranslations from './locales/en.json';

// Configuration des ressources de traduction
const resources = {
  fr: {
    translation: frTranslations,
  },
  en: {
    translation: enTranslations,
  },
};

// Configuration i18next
i18n
  // Détection automatique de la langue
  .use(LanguageDetector)
  // Backend pour charger les traductions
  .use(Backend)
  // Intégration avec React
  .use(initReactI18next)
  // Initialisation
  .init({
    // Ressources de traduction
    resources,
    
    // Langue par défaut
    fallbackLng: 'fr', // Français par défaut pour le Cameroun
    
    // Langues supportées
    supportedLngs: ['fr', 'en'],
    
    // Configuration de détection de langue
    detection: {
      // Ordre de détection
      order: [
        'localStorage',
        'navigator',
        'htmlTag',
        'path',
        'subdomain',
      ],
      
      // Clé de stockage local
      lookupLocalStorage: 'chopexpress-language',
      
      // Cache la langue détectée
      caches: ['localStorage'],
      
      // Exclure certaines langues de la détection automatique
      excludeCacheFor: ['cimode'],
    },
    
    // Configuration du backend
    backend: {
      // Chemin vers les fichiers de traduction
      loadPath: '/locales/{{lng}}.json',
      
      // Ajouter un timestamp pour éviter le cache
      addPath: '/locales/add/{{lng}}/{{ns}}',
    },
    
    // Interpolation
    interpolation: {
      // React échappe déjà les valeurs
      escapeValue: false,
      
      // Format des variables
      formatSeparator: ',',
      
      // Fonctions de formatage personnalisées
      format: (value, format, lng) => {
        if (format === 'uppercase') return value.toUpperCase();
        if (format === 'lowercase') return value.toLowerCase();
        if (format === 'currency') {
          // Format monétaire pour le Cameroun (FCFA)
          return new Intl.NumberFormat(lng === 'fr' ? 'fr-CM' : 'en-CM', {
            style: 'currency',
            currency: 'XAF',
            minimumFractionDigits: 0,
          }).format(value);
        }
        if (format === 'date') {
          return new Intl.DateTimeFormat(lng === 'fr' ? 'fr-CM' : 'en-CM').format(new Date(value));
        }
        return value;
      },
    },
    
    // Configuration React
    react: {
      // Utiliser Suspense pour le chargement asynchrone
      useSuspense: true,
      
      // Bind i18n instance
      bindI18n: 'languageChanged',
      
      // Bind i18n store
      bindI18nStore: '',
      
      // Délai de transition
      transEmptyNodeValue: '',
      
      // Clés de traduction manquantes
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i'],
    },
    
    // Mode debug (uniquement en développement)
    debug: process.env.NODE_ENV === 'development',
    
    // Namespace par défaut
    defaultNS: 'translation',
    
    // Séparateur de namespace
    nsSeparator: ':',
    
    // Séparateur de clé
    keySeparator: '.',
    
    // Retourner les objets au lieu des chaînes
    returnObjects: false,
    
    // Retourner les détails de traduction
    returnDetails: false,
    
    // Joindre les arrays
    joinArrays: false,
    
    // Post-traitement
    postProcess: false,
    
    // Retourner null pour les clés manquantes
    returnNull: false,
    
    // Retourner une chaîne vide pour les clés manquantes
    returnEmptyString: false,
    
    // Fonction de traitement des clés manquantes
    missingKeyHandler: (lng, ns, key, fallbackValue) => {
      if (process.env.NODE_ENV === 'development') {
        console.warn(`Clé de traduction manquante: ${key} pour la langue: ${lng}`);
      }
    },
    
    // Fonction de sauvegarde des traductions manquantes
    saveMissing: process.env.NODE_ENV === 'development',
  });

// Export de l'instance i18n configurée
export default i18n;

// Utilitaires pour la gestion des langues
export const changeLanguage = (lng: string) => {
  return i18n.changeLanguage(lng);
};

export const getCurrentLanguage = () => {
  return i18n.language;
};

export const getSupportedLanguages = () => {
  return ['fr', 'en'];
};

export const getLanguageDisplayName = (lng: string) => {
  const names: Record<string, string> = {
    fr: 'Français',
    en: 'English',
  };
  return names[lng] || lng;
};

// Direction du texte (pour le support RTL futur)
export const getTextDirection = (lng: string) => {
  // Toutes les langues supportées sont LTR pour l'instant
  return 'ltr';
};