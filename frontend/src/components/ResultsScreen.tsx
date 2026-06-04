import { useTrip } from '../state/trip'
import { deltaStr, money } from '../util'

export function ResultsScreen() {
  const { snapshot, answer, busy } = useTrip()
  const r = snapshot?.results
  if (!r) return null
  return (
    <div className="results-card">
      <div className="res-hero">
        <div className="res-emoji">🎯</div>
        <div className="res-h-ttl">Поездка завершена</div>
        <div className="res-h-sub">Астана · 5–7 июня · бюджет план/факт</div>
      </div>
      <table className="res-table">
        <thead>
          <tr><th>Категория</th><th>План</th><th>Факт</th><th>±</th></tr>
        </thead>
        <tbody>
          {r.rows.map((row) => (
            <tr key={row.category}>
              <td>{row.category}</td>
              <td>{money(row.plan)}</td>
              <td>{money(row.fact)}</td>
              <td className={`delta ${row.delta <= 0 ? 'neg' : 'pos'}`}>{deltaStr(row.delta)}</td>
            </tr>
          ))}
          <tr className="total">
            <td>Итого</td>
            <td>{money(r.totals.plan)}</td>
            <td>{money(r.totals.fact)}</td>
            <td className={`delta ${r.totals.delta <= 0 ? 'neg' : 'pos'}`}>{deltaStr(r.totals.delta)} 🎯</td>
          </tr>
        </tbody>
      </table>
      <div className="res-bonus">✦ Бонусы Halyk+: начислено <b>{money(r.bonuses.earned)}</b>. {r.bonuses.note}</div>
      <div className="fly-ttl">Куда дальше?</div>
      <div className="flywheel">
        {r.flywheel.map((f) => (
          <div key={f.value} className="fly-card" onClick={() => !busy && answer(f.value)}>
            <div className="fly-emoji">{f.emoji}</div>
            <div className="fly-name">{f.label}</div>
            <div className="fly-sub">{f.sub}</div>
            <div className="fly-price">{f.price}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
