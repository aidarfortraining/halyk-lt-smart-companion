// Four typed fetch wrappers to the trip API (ARCHITECTURE.md §6, §8).
import type { Snapshot } from '../types'

const BASE = '/api'

async function request(path: string, init?: RequestInit): Promise<Snapshot> {
  const res = await fetch(BASE + path, init)
  if (!res.ok) throw new Error(`${init?.method ?? 'GET'} ${path} → ${res.status}`)
  return res.json()
}

function post(path: string, body?: unknown): Promise<Snapshot> {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  })
}

export const api = {
  start: () => post('/trip/start'),
  state: (id: number) => request(`/trip/${id}/state`),
  answer: (id: number, chip_value: string) => post(`/trip/${id}/answer`, { chip_value }),
  advance: (id: number, to_phase: number) => post(`/trip/${id}/advance`, { to_phase }),
}
