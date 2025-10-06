
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig(({ mode }) => {
  const isWebComponent = mode === 'webcomponent';

  return {
    plugins: [react()],
    build: {
      outDir: isWebComponent ? 'dist/webcomponent' : 'dist/standalone',
      lib: isWebComponent ? {
        entry: resolve(__dirname, 'src/webcomponent/index.ts'),
        name: 'RagChatComponent',
        fileName: 'rag-chat',
        formats: ['iife']
      } : undefined,
      rollupOptions: isWebComponent ? {
        output: {
          inlineDynamicImports: true,
          assetFileNames: 'rag-chat.[ext]'
        }
      } : undefined,
      minify: 'terser',
      sourcemap: true
    },
    define: {
      'process.env.NODE_ENV': JSON.stringify(mode)
    }
  };
});

