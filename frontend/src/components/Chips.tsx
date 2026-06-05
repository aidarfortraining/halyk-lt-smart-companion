import { useTrip } from '../state/trip'

export function Chips() {
  const { snapshot, answer, busy } = useTrip()
  // Flywheel chips are rendered inside ResultsScreen; suppress here on phase 4.
  // A text-input step (e.g. typing a stay address) awaits input but has no chips.
  if (!snapshot?.await_user || snapshot.results || snapshot.chips.length === 0) return null
  return (
    <div className="chips-wrap">
      <div className="chips-ctx">Ваш ответ <span className="ctx-badge">выберите</span></div>
      <div className="chips">
        {snapshot.chips.map((c) => (
          <div key={c.value} className="chip" onClick={() => !busy && answer(c.value)}>
            <div className="chip-l">{c.label}</div>
            {c.sub && <div className="chip-s">{c.sub}</div>}
          </div>
        ))}
      </div>
    </div>
  )
}
