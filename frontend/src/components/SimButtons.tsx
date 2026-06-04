import { useTrip } from '../state/trip'

const SIM: Record<number, { to: number; label: string }> = {
  0: { to: 1, label: '▶ Симуляция: за 3 дня до поездки' },
  1: { to: 2, label: '▶ В поезде, за 40 минут до Астаны' },
  2: { to: 3, label: '▶ Выходные в Астане' },
  3: { to: 4, label: '▶ Итоги поездки' },
}

export function SimButtons() {
  const { snapshot, advance, busy } = useTrip()
  if (!snapshot || snapshot.await_user || snapshot.phase >= 4) return null
  const sim = SIM[snapshot.phase]
  if (!sim) return null
  return (
    <div className="sim-wrap">
      <button className="sim-btn" disabled={busy} onClick={() => advance(sim.to)}>{sim.label}</button>
    </div>
  )
}
