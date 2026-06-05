// Render smoke test (jsdom) — mounts <App/> against real captured snapshots and asserts the
// chat + Travel Plan + Results render without runtime errors. Substitutes for the browser
// click-through when Playwright isn't available. Assertions target deterministic UI (structure,
// chips, plan, budget, Итоги table) — NOT the LLM-generated message text.
import { cleanup, render, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import phase0 from './fixtures.phase0.json'
import phase4 from './fixtures.phase4.json'
import type { Snapshot } from './types'

const P0 = phase0 as unknown as Snapshot
const P4 = phase4 as unknown as Snapshot

vi.mock('./api/client', () => ({
  api: { start: vi.fn(), reset: vi.fn(), state: vi.fn(), answer: vi.fn(), advance: vi.fn() },
}))

import { api } from './api/client'
import App from './App'

// Skip the ticket-purchase wizard so <App/> mounts straight into the companion.
beforeEach(() => {
  localStorage.setItem('halyk_purchased', '1')
  vi.mocked(api.start).mockResolvedValue(P0)
})
afterEach(() => { cleanup(); localStorage.clear() })

test('mounts and renders the phase-0 chat + Travel Plan', async () => {
  const { container } = render(<App />)
  await waitFor(() => expect(container.querySelector('.bub.ai')).toBeTruthy())
  const text = container.textContent ?? ''

  expect(container.querySelectorAll('.pi').length).toBe(10)        // 10 plan rows
  expect(container.querySelectorAll('.chip').length).toBe(3)       // hotel chips
  expect(text).toContain('Жильё · Booking')
  expect(text).toContain('Такси с вокзала')
  expect(text).toContain('Экстренная помощь')                     // emergency block
  expect(container.querySelector('.b-total')?.textContent ?? '').toMatch(/175.000/)
  expect(container.querySelectorAll('.phase').length).toBe(5)      // phase bar
  expect(container.querySelectorAll('.phase.active').length).toBe(1)
})

test('renders the Итоги table + Flywheel at phase 4', async () => {
  vi.mocked(api.start).mockResolvedValue(P4)
  const { container } = render(<App />)
  await waitFor(() => expect(container.querySelector('.results-card')).toBeTruthy())

  expect(container.querySelectorAll('.fly-card').length).toBe(3)   // 3 next-trip cards
  expect(container.textContent ?? '').toContain('Бурабай')
  const total = container.querySelector('.res-table tr.total')?.textContent ?? ''
  expect(total).toMatch(/175.000/)        // plan
  expect(total).toMatch(/169.500/)        // fact 🎯
})
