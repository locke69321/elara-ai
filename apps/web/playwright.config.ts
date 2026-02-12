import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/browser-contract',
  fullyParallel: true,
  reporter: 'list',
  use: {
    browserName: 'chromium',
    headless: true,
    viewport: { width: 1366, height: 900 },
  },
})
