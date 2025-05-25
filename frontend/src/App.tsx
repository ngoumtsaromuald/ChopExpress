import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

// Import des composants
import Layout from './components/Layout';
import MenuPage from './pages/MenuPage';
import Dashboard from './pages/Dashboard';
import Orders from './pages/Orders';
import Restaurants from './pages/Restaurants';
import Settings from './pages/Settings';
import LoadingSpinner from './components/ui/LoadingSpinner';

// Import de la configuration i18n
import './i18n/config';

// Configuration React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const { i18n } = useTranslation();

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50" dir={i18n.dir()}>
          <Suspense fallback={<LoadingSpinner />}>
            <Layout>
              <Routes>
                {/* Page d'accueil - Dashboard */}
                <Route path="/" element={<Dashboard />} />
                
                {/* Page Menu - Livrable initial */}
                <Route path="/menu" element={<MenuPage />} />
                
                {/* Pages d'administration */}
                <Route path="/orders" element={<Orders />} />
                <Route path="/restaurants" element={<Restaurants />} />
                <Route path="/settings" element={<Settings />} />
                
                {/* Route par défaut */}
                <Route path="*" element={<MenuPage />} />
              </Routes>
            </Layout>
          </Suspense>
          
          {/* Notifications toast */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#4ade80',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </Router>
      
      {/* React Query DevTools (uniquement en développement) */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}

export default App;