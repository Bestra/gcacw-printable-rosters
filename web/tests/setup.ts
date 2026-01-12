import '@testing-library/jest-dom'

// Mock import.meta.env.BASE_URL for tests
Object.defineProperty(import.meta, 'env', {
  value: {
    BASE_URL: '/',
    MODE: 'test',
    DEV: false,
    PROD: false,
    SSR: false,
  },
})
