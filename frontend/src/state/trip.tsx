// Trip state: Context + useReducer. Every API response replaces the snapshot wholesale
// (ARCHITECTURE.md §8) — simple and predictable.
import {
  createContext, useContext, useEffect, useReducer, useRef,
  type ReactNode,
} from 'react'
import { api } from '../api/client'
import type { Snapshot } from '../types'

interface State {
  snapshot: Snapshot | null
  busy: boolean
}

type Action =
  | { type: 'snapshot'; payload: Snapshot }
  | { type: 'busy'; payload: boolean }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'snapshot':
      return { snapshot: action.payload, busy: false }
    case 'busy':
      return { ...state, busy: action.payload }
  }
}

interface TripContext {
  snapshot: Snapshot | null
  busy: boolean
  answer: (chipValue: string) => Promise<void>
  advance: (toPhase: number) => Promise<void>
  reset: () => Promise<void>
}

const Ctx = createContext<TripContext | null>(null)

export function TripProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, { snapshot: null, busy: false })
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return // guard React 18 StrictMode double-mount
    started.current = true
    // Page load = resume where we left off (start is idempotent). The ↻ button resets.
    api.start().then((s) => dispatch({ type: 'snapshot', payload: s }))
  }, [])

  const run = async (fn: () => Promise<Snapshot>) => {
    dispatch({ type: 'busy', payload: true })
    try {
      dispatch({ type: 'snapshot', payload: await fn() })
    } catch {
      dispatch({ type: 'busy', payload: false })
    }
  }

  const value: TripContext = {
    snapshot: state.snapshot,
    busy: state.busy,
    answer: (chipValue) => {
      const id = state.snapshot?.trip.id
      return id ? run(() => api.answer(id, chipValue)) : Promise.resolve()
    },
    advance: (toPhase) => {
      const id = state.snapshot?.trip.id
      return id ? run(() => api.advance(id, toPhase)) : Promise.resolve()
    },
    reset: () => run(() => api.reset()),
  }

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useTrip(): TripContext {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useTrip must be used within TripProvider')
  return ctx
}
