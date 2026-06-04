import { useTrip } from '../state/trip'
import { money } from '../util'

export function Budget() {
  const { snapshot } = useTrip()
  if (!snapshot) return null
  const b = snapshot.budget
  const pct = b.total ? Math.round((b.fact / b.total) * 100) : 0
  const vars = b.lines.filter((l) => l.kind === 'variable')
  return (
    <div className="budget">
      <div className="b-hdr">
        <div className="b-lbl">Бюджет поездки</div>
        <div className="b-total">{money(b.total)}</div>
      </div>
      <div className="brow"><span className="brow-n">✓ Факт</span><span className="brow-v g">{money(b.fact)}</span></div>
      <div className="brow"><span className="brow-n">Расчётное</span><span className="brow-v gr">{money(b.estimate)}</span></div>
      <div className="btr"><div className="btr-f" style={{ width: `${pct}%` }} /></div>
      {snapshot.phase >= 3 && (
        <div className="tracker-cats">
          {vars.map((l) => {
            const over = l.fact_amount != null && l.fact_amount > l.plan_amount
            return (
              <div key={l.category} className="tcat">
                <span className="tcat-n">{l.category}</span>
                <span className={`tcat-v ${over ? 'over' : ''}`}>
                  {money(l.fact_amount ?? l.plan_amount)}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
