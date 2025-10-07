
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig(({ mode }) => {
  const isWebComponent = mode === 'webcomponent';
  const isLib = mode === 'lib';

  return {
    plugins: [react()],
    build: {
      outDir: isWebComponent ? 'dist/webcomponent' : isLib ? 'dist' : 'dist/standalone',
      lib: isWebComponent
        ? {
            entry: resolve(__dirname, 'src/webcomponent/index.ts'),
            name: 'RagChatComponent',
            fileName: 'rag-chat',
            formats: ['iife']
          }
        : isLib
        ? {
            entry: resolve(__dirname, 'src/lib/index.ts'),
            name: 'RagChatComponent',
            fileName: (format) => `index.${format}.js`,
            formats: ['es', 'cjs', 'umd']
          }
        : undefined,
      rollupOptions: isWebComponent
        ? {
            output: {
              inlineDynamicImports: true,
              assetFileNames: 'rag-chat.[ext]'
            }
          }
        : isLib
        ? {
            external: ['react', 'react-dom'],
            output: {
              globals: { react: 'React', 'react-dom': 'ReactDOM' }
            }
          }
        : undefined,
      // Use Vite's default (esbuild) minifier
      sourcemap: true
    },
    define: {
      'process.env.NODE_ENV': JSON.stringify(mode)
    }
  };
});

