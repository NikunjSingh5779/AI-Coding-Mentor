import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, root, '');

  return {
    base: './',
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(root, './src'),
      },
    },
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target: env.VITE_PROXY_API_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
        '/ws': {
          target: env.VITE_PROXY_WS_URL || 'ws://localhost:8000',
          ws: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            monaco: ['@monaco-editor/react', 'monaco-editor'],
          },
        },
      },
    },
    define: {
      __APP_VERSION__: JSON.stringify(env.npm_package_version || '1.0.0'),
    },
    optimizeDeps: {
      include: ['react', 'react-dom', '@monaco-editor/react'],
    },
  };
});
