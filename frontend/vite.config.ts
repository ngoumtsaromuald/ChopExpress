import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Configuration Vite pour ChopExpress Frontend
export default defineConfig({
  plugins: [react()],
  
  // Résolution des chemins
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
      '@services': path.resolve(__dirname, './src/services'),
      '@store': path.resolve(__dirname, './src/store'),
      '@i18n': path.resolve(__dirname, './src/i18n'),
      '@assets': path.resolve(__dirname, './src/assets'),
    },
  },
  
  // Configuration du serveur de développement
  server: {
    port: 3000,
    host: true, // Permet l'accès depuis d'autres appareils
    open: true, // Ouvre automatiquement le navigateur
    cors: true,
    proxy: {
      // Proxy vers l'API backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // Proxy pour les webhooks de développement
      '/webhook': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  
  // Configuration de build
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'terser',
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          // Séparation des chunks pour optimiser le chargement
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
          i18n: ['react-i18next', 'i18next'],
          charts: ['recharts'],
          maps: ['mapbox-gl', 'react-map-gl'],
        },
      },
    },
    // Optimisation des chunks
    chunkSizeWarningLimit: 1000,
  },
  
  // Configuration des variables d'environnement
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
  
  // Configuration CSS
  css: {
    postcss: './postcss.config.js',
    devSourcemap: true,
  },
  
  // Configuration des tests
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
  },
  
  // Optimisation des dépendances
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'react-i18next',
      'i18next',
      '@tanstack/react-query',
      'axios',
      'zustand',
      'react-hook-form',
      'zod',
      'date-fns',
      'lucide-react',
    ],
    exclude: ['@mapbox/mapbox-gl-language'],
  },
  
  // Configuration pour le mode preview
  preview: {
    port: 4173,
    host: true,
    cors: true,
  },
  
  // Variables d'environnement publiques
  envPrefix: 'VITE_',
});