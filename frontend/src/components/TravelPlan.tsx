import { useTrip } from '../state/trip'
import { money } from '../util'
import { Budget } from './Budget'
import { EmergencyBlock } from './EmergencyBlock'

const PHASE_LABELS = ['Сейчас', 'За 3 дня', 'В пути', 'В Астане', 'Итоги']

export function TravelPlan() {
  const { snapshot } = useTrip()
  if (!snapshot) return <div className="plan-col" />
  const ticketPrice = snapshot.budget.lines.find((l) => l.category === 'Билеты ЖД')?.fact_amount ?? 38000
  return (
    <div className="plan-col">
      <div className="plan-hdr">
        <div className="plan-ttl">Ваш план поездки</div>
        <div className="ticket">
          <div className="t-route">АЛА → АСТ</div>
          <div className="t-meta">🚆 {snapshot.trip.transport} · 5–7 июня · {snapshot.trip.pax} чел.</div>
          <div className="t-foot">
            <span className="t-price">{money(ticketPrice)}</span>
            <span className="t-ok">✓ Оплачено</span>
          </div>
        </div>
        <div className="phase-bar">
          {PHASE_LABELS.map((l, i) => (
            <div key={l} className={`phase ${i <= snapshot.phase ? 'active' : ''}`} />
          ))}
        </div>
        <div className="phase-labels">{PHASE_LABELS.map((l) => <span key={l}>{l}</span>)}</div>
      </div>

      <div className="plan-items">
        {snapshot.plan.map((it) => (
          <div className="pi" key={it.key}>
            <div className={`pi-ico ${it.state}`}>{it.icon}</div>
            <div className="pi-body">
              <div className="pi-svc">{it.service}</div>
              <div className={`pi-val ${it.state}`}>{it.value}</div>
              {it.tag && <span className={`pi-tag ${it.tag}`}>{it.tag === 'a' ? '⚠ уточнить' : '✓'}</span>}
            </div>
          </div>
        ))}
      </div>

      <Budget />
      <EmergencyBlock />
      <div className="plan-ftr">
        <div className="plan-hint">✦ AI напомнит про каждый шаг в нужный момент</div>
      </div>
    </div>
  )
}
