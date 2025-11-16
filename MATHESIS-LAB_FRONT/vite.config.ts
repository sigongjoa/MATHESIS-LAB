import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

/**
 * 테스트 설정 파일 읽기
 * 중앙화된 설정으로 포트 등을 동적으로 설정
 */
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const configPath = path.resolve(__dirname, '../test.config.json');
let testConfig: any = {
  frontend: { port: 3002, host: '0.0.0.0' },
  backend: { port: 8000, host: '0.0.0.0' }
};

if (fs.existsSync(configPath)) {
  testConfig = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
}

const FRONTEND_PORT = process.env.FRONTEND_PORT || testConfig.frontend.port;
const FRONTEND_HOST = process.env.FRONTEND_HOST || testConfig.frontend.host;
const BACKEND_PORT = process.env.BACKEND_PORT || testConfig.backend.port;
const BACKEND_HOST = process.env.BACKEND_HOST || testConfig.backend.host;

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      server: {
        port: FRONTEND_PORT,
        host: FRONTEND_HOST,
        proxy: {
          '/api': {
            target: `http://${BACKEND_HOST}:${BACKEND_PORT}`,
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, '/api'),
          },
        },
      },
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      test: {
        globals: true,
        environment: 'jsdom',
        testTimeout: 10000,
        pool: 'threads',
        poolOptions: {
          threads: {
            singleThread: true,
          },
        },
        include: ['**/*.test.{ts,tsx}'],
        exclude: ['node_modules', 'dist', '.idea', '.git', '.cache', 'e2e'],
      },
    };
});
