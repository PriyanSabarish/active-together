import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

const dep = (name) => fileURLToPath(new URL(`./node_modules/${name}`, import.meta.url))

export default defineConfig({
  plugins: [vue()],
  resolve: {
    // Spec files in ../test sit outside this package, so bare imports
    // must be pointed back at client/node_modules explicitly.
    alias: {
      vue: dep('vue'),
      pinia: dep('pinia'),
      'vue-router': dep('vue-router'),
      '@vue/test-utils': dep('@vue/test-utils')
    }
  },
  // The spec files live in ../test, outside the vite root.
  server: { fs: { allow: ['..'] } },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['../test/**/*.spec.js'],
    coverage: {
      provider: 'v8',
      reportOnFailure: true,
      include: ['src/**/*.{js,vue}'],
      exclude: ['src/main.js'],
      reporter: ['text', 'html'],
      reportsDirectory: '../test/coverage'
    }
  }
})
