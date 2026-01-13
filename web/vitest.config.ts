/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    // scripts/*.test.tsx are included here but excluded from default npm test runs
    // (they're slow generators). Run explicitly: npx vitest run scripts/generate-snapshots.test.tsx
    include: ['tests/**/*.test.ts', 'tests/**/*.test.tsx', 'scripts/**/*.test.tsx'],
  },
})
