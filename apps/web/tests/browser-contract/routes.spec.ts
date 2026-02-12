import { readFileSync } from 'node:fs'

import { expect, test } from '@playwright/test'

function read(path: string): string {
  return readFileSync(new URL(path, import.meta.url), 'utf8')
}

test('route modules expose interactive affordances', async () => {
  const companionSource = read('../../src/routes/companion.tsx')
  const executionSource = read('../../src/routes/execution.tsx')
  const studioSource = read('../../src/routes/agent-studio.tsx')

  expect(companionSource).toContain('companion-message-input')
  expect(companionSource).toContain('memory-hit-chip')
  expect(executionSource).toContain('execution-goal-input')
  expect(executionSource).toContain('status="required"')
  expect(executionSource).toContain('replay-resume-controls')
  expect(studioSource).toContain('specialist-list')
  expect(studioSource).toContain('specialist-form')
})

test('route grid contract is desktop friendly', async ({ page }) => {
  const css = read('../../src/styles/tokens.css')
  await page.setViewportSize({ width: 1200, height: 900 })
  await page.setContent(`
    <style>${css}</style>
    <section class="route-grid"><article>A</article><article>B</article></section>
  `)

  const columnCount = await page.evaluate(() => {
    const element = document.querySelector('.route-grid')
    if (element === null) {
      return ''
    }
    return getComputedStyle(element).gridTemplateColumns
  })

  const columns = columnCount.split(' ').filter((value) => value.length > 0)
  expect(columns.length).toBeGreaterThanOrEqual(2)
})

test('route grid contract collapses to a single column on mobile', async ({ page }) => {
  const css = read('../../src/styles/tokens.css')
  await page.setViewportSize({ width: 640, height: 900 })
  await page.setContent(`
    <style>${css}</style>
    <section class="route-grid"><article>A</article><article>B</article></section>
  `)

  const columnCount = await page.evaluate(() => {
    const element = document.querySelector('.route-grid')
    if (element === null) {
      return ''
    }
    return getComputedStyle(element).gridTemplateColumns
  })

  const columns = columnCount.split(' ').filter((value) => value.length > 0)
  expect(columns.length).toBe(1)
})
