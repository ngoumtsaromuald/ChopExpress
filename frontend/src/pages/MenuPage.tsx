import React from 'react';
import { useTranslation } from 'react-i18next';
import { ChefHat, Clock, MapPin, Star } from 'lucide-react';

const MenuPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="container mx-auto px-4 py-8">
      {/* En-tête de la page */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {t('menu.title', 'Menu des Restaurants')}
        </h1>
        <p className="text-gray-600">
          {t('menu.subtitle', 'Découvrez les délicieux plats disponibles via ChopExpress')}
        </p>
      </div>

      {/* État vide - Page en construction */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
        <div className="text-center">
          {/* Icône principale */}
          <div className="mx-auto w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mb-6">
            <ChefHat className="w-12 h-12 text-green-600" />
          </div>
          
          {/* Titre et description */}
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            {t('menu.empty.title', 'Menu en cours de préparation')}
          </h2>
          <p className="text-gray-600 mb-8 max-w-md mx-auto">
            {t('menu.empty.description', 'Nos chefs préparent une sélection exceptionnelle de plats. Cette page sera bientôt remplie de délicieuses options!')}
          </p>
          
          {/* Fonctionnalités à venir */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <MapPin className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-medium text-gray-900 mb-1">
                {t('menu.features.location', 'Géolocalisation')}
              </h3>
              <p className="text-sm text-gray-600">
                {t('menu.features.location_desc', 'Restaurants près de vous')}
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
              <h3 className="font-medium text-gray-900 mb-1">
                {t('menu.features.delivery', 'Livraison rapide')}
              </h3>
              <p className="text-sm text-gray-600">
                {t('menu.features.delivery_desc', 'Suivi en temps réel')}
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Star className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-medium text-gray-900 mb-1">
                {t('menu.features.quality', 'Qualité premium')}
              </h3>
              <p className="text-sm text-gray-600">
                {t('menu.features.quality_desc', 'Plats sélectionnés')}
              </p>
            </div>
          </div>
          
          {/* Bouton d'action (désactivé pour l'instant) */}
          <div className="mt-8">
            <button 
              disabled
              className="bg-gray-300 text-gray-500 px-6 py-3 rounded-lg font-medium cursor-not-allowed"
            >
              {t('menu.coming_soon', 'Bientôt disponible')}
            </button>
          </div>
        </div>
      </div>
      
      {/* Informations de développement */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600 text-sm font-medium">ℹ</span>
            </div>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-900">
              {t('dev.info.title', 'Information de développement')}
            </h3>
            <p className="text-sm text-blue-700 mt-1">
              {t('dev.info.description', 'Cette page fait partie du livrable initial ChopExpress. L\'intégration avec l\'API backend et la base de données Supabase sera implémentée dans les prochaines itérations.')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MenuPage;