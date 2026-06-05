// Snapshot shape returned by every API endpoint (ARCHITECTURE.md §6).

export type PlanState = 'locked' | 'wait' | 'done'
export type MessageKind = 'ai' | 'user' | 'time' | 'concern' | 'sys' | 'results'

export interface Trip {
  id: number
  route: string
  transport: string
  depart_at: string
  arrive_at: string
  pax: number
  kids: { name: string; age: number }[]
  hotel_name: string
  hotel_address: string
  is_apartments: boolean
  weather: { fri?: string; sat?: string; sun?: string }
  phase: number
  step_index: number
}

export interface PlanItem {
  key: string
  order: number
  icon: string
  service: string
  phase: number
  state: PlanState
  value: string
  tag: string
  badge: string
}

export interface Message {
  order: number
  kind: MessageKind
  text: string
  meta: { level?: string; title?: string; sub?: string; hint?: string }
}

export interface BudgetLine {
  category: string
  plan_amount: number
  fact_amount: number | null
  kind: 'prepaid' | 'variable'
  order: number
}

export interface Budget {
  fact: number
  estimate: number
  total: number
  lines: BudgetLine[]
}

export interface Chip {
  label: string
  sub: string
  value: string
}

export interface ResultsRow {
  category: string
  plan: number
  fact: number
  delta: number
}

export interface FlywheelTrip {
  emoji: string
  label: string
  sub: string
  price: string
  value: string
}

export interface Results {
  rows: ResultsRow[]
  totals: { plan: number; fact: number; delta: number }
  bonuses: { earned: number; tier: string; note: string }
  flywheel: FlywheelTrip[]
}

export interface Emergency {
  label: string
  value: string
}

export interface Snapshot {
  trip: Trip
  plan: PlanItem[]
  messages: Message[]
  budget: Budget
  emergency: Emergency[]
  phase: number
  chips: Chip[]
  await_user: boolean
  input_hint: string
  results: Results | null
}
