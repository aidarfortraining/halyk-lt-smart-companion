// V1 ticket-purchase wizard (prototype steps 1–3): find → pick → buy → companion.
// Static, no AI, no backend — content matches the seeded reference scenario so the handoff
// to the companion is seamless. The "Кто едет" row is display-only (the document-expiry alert
// is intentionally a companion differentiator, not spoiled here).
import { useState } from 'react'
import '../../styles/wizard.css'

type Transport = 'avia' | 'zhd' | 'bus'

interface Leg {
  d: string; a: string; from: string; to: string; date: string; dur: string
}
interface Ticket {
  id: string; carrier: string; type: string; price: number
  tag?: string; tagColor?: string; tagBg?: string
  there: Leg; back: Leg
}

const TICKETS: Record<Transport, Ticket[]> = {
  zhd: [
    { id: 'night', carrier: 'Ночной поезд · купе', type: 'Halyk Travel · туда-обратно', tag: 'Рекомендуем', price: 38000,
      there: { d: '20:00', a: '09:00', from: 'Алматы', to: 'Астана', date: '4→5 июня', dur: '~13 ч' },
      back: { d: '21:30', a: '10:30', from: 'Астана', to: 'Алматы', date: '7→8 июня', dur: '~13 ч' } },
    { id: 'platz', carrier: 'Поезд · плацкарт', type: 'Halyk Travel · ночной', tag: 'Дёшево', tagColor: '#92400E', tagBg: '#FEF3C7', price: 22000,
      there: { d: '19:40', a: '09:10', from: 'Алматы', to: 'Астана', date: '4→5 июня', dur: '~13 ч' },
      back: { d: '21:00', a: '10:30', from: 'Астана', to: 'Алматы', date: '7→8 июня', dur: '~13 ч' } },
    { id: 'sv', carrier: 'Поезд · СВ (люкс)', type: 'Halyk Travel · туда-обратно', tag: 'Премиум', tagColor: '#6D28D9', tagBg: '#EDE9FE', price: 72000,
      there: { d: '20:00', a: '09:00', from: 'Алматы', to: 'Астана', date: '4→5 июня', dur: '~13 ч' },
      back: { d: '21:30', a: '10:30', from: 'Астана', to: 'Алматы', date: '7→8 июня', dur: '~13 ч' } },
  ],
  avia: [
    { id: 'airastana', carrier: 'Air Astana', type: 'Halyk Travel · KC 853', tag: 'Быстро', tagColor: '#1D4ED8', tagBg: '#DBEAFE', price: 65000,
      there: { d: '08:00', a: '09:40', from: 'Алматы', to: 'Астана', date: '5 июня', dur: '1 ч 40 м' },
      back: { d: '20:00', a: '21:40', from: 'Астана', to: 'Алматы', date: '7 июня', dur: '1 ч 40 м' } },
    { id: 'flyarystan', carrier: 'FlyArystan', type: 'Halyk Travel · KC 121', price: 52000,
      there: { d: '14:00', a: '15:45', from: 'Алматы', to: 'Астана', date: '5 июня', dur: '1 ч 45 м' },
      back: { d: '16:00', a: '17:45', from: 'Астана', to: 'Алматы', date: '7 июня', dur: '1 ч 45 м' } },
  ],
  bus: [
    { id: 'bus', carrier: 'Автобус · Lux', type: 'Halyk Travel · туда-обратно', tag: 'Дёшево', tagColor: '#92400E', tagBg: '#FEF3C7', price: 12000,
      there: { d: '21:00', a: '09:00', from: 'Алматы', to: 'Астана', date: '4→5 июня', dur: '12 ч' },
      back: { d: '21:00', a: '09:00', from: 'Астана', to: 'Алматы', date: '7→8 июня', dur: '12 ч' } },
  ],
}

const PASSENGERS = [
  { av: 'А', kid: false, name: 'Айдар Абдрахманов', sub: 'Взрослый · вагон 5, место 12' },
  { av: 'Ал', kid: false, name: 'Алия Абдрахманова', sub: 'Взрослый · место 13' },
  { av: '9', kid: true, name: 'Айша Абдрахманова', sub: 'Ребёнок 9 лет · место 14' },
  { av: '5', kid: true, name: 'Тимур Абдрахманов', sub: 'Ребёнок 5 лет · место 15' },
]

const META: Record<number, [string, string]> = {
  1: ['Куда поедете?', 'Найдём билеты и соберём всю поездку'],
  2: ['Билеты Алматы → Астана', '5–7 июня · туда-обратно · 4 пассажира'],
  3: ['Ваш билет', 'Halyk Travel · оплата картой Halyk'],
}

const fmt = (n: number) => n.toLocaleString('ru-RU').replace(/ /g, ' ').replace(/,/g, ' ') + ' ₸'
const icon = (t: Transport) => (t === 'avia' ? '✈️' : t === 'bus' ? '🚌' : '🚄')
const ticketById = (id: string): Ticket => {
  for (const k of Object.keys(TICKETS) as Transport[]) {
    const found = TICKETS[k].find((x) => x.id === id)
    if (found) return found
  }
  return TICKETS.zhd[0]
}

function TicketCard({ t, selected, onClick }: { t: Ticket; selected: boolean; onClick: () => void }) {
  return (
    <div className={`ticket ${selected ? 'selected' : ''}`} onClick={onClick}>
      <div className="ticket-top">
        <span style={{ fontSize: 22 }}>{icon(t.id === 'airastana' || t.id === 'flyarystan' ? 'avia' : t.id === 'bus' ? 'bus' : 'zhd')}</span>
        <div style={{ flex: 1 }}>
          <div className="ticket-carrier">{t.carrier}</div>
          <div className="ticket-type">{t.type}</div>
        </div>
        {t.tag && (
          <span className="ticket-tag" style={t.tagBg ? { background: t.tagBg, color: t.tagColor } : undefined}>{t.tag}</span>
        )}
      </div>
      <div className="ticket-route">
        <div><div className="ticket-time">{t.there.d}</div><div className="ticket-city">{t.there.from} · {t.there.date}</div></div>
        <div className="ticket-mid"><div className="ticket-dur">{t.there.dur}</div><div className="ticket-arrow" /></div>
        <div style={{ textAlign: 'right' }}><div className="ticket-time">{t.there.a}</div><div className="ticket-city">{t.there.to} · {t.there.date}</div></div>
      </div>
      <div className="ticket-foot">
        <span className="ticket-price">{fmt(t.price)}</span>
        <span style={{ fontSize: 12, color: 'var(--muted)' }}>за 4 · туда-обратно</span>
      </div>
    </div>
  )
}

function Legs({ t }: { t: Ticket }) {
  const leg = (label: string, l: Leg) => (
    <>
      <div className="leg-tag">{label} · {l.date}</div>
      <div className="ticket-route">
        <div><div className="ticket-time">{l.d}</div><div className="ticket-city">{l.from}</div></div>
        <div className="ticket-mid"><div className="ticket-dur">{l.dur}</div><div className="ticket-arrow" /></div>
        <div style={{ textAlign: 'right' }}><div className="ticket-time">{l.a}</div><div className="ticket-city">{l.to}</div></div>
      </div>
    </>
  )
  return (
    <>
      {leg('Туда', t.there)}
      <div style={{ marginTop: 14 }}>{leg('Обратно', t.back)}</div>
    </>
  )
}

export function Wizard({ onBuy }: { onBuy: () => void }) {
  const [step, setStep] = useState(1)
  const [transport, setTransport] = useState<Transport>('zhd')
  const [ticketId, setTicketId] = useState('night')

  const t = ticketById(ticketId)
  const [title, sub] = META[step]

  const pickTransport = (tr: Transport) => {
    setTransport(tr)
    if (!TICKETS[tr].some((x) => x.id === ticketId)) setTicketId(TICKETS[tr][0].id)
  }
  const restart = () => { setStep(1); setTransport('zhd'); setTicketId('night') }

  return (
    <div className="wizard-root">
      <div className="topbar">
        <div className="brand"><div className="logo">H</div><b>Halyk</b><small>Smart Travel</small></div>
        <div className="stepper">
          <span className="step-text">Шаг {step} из 3</span>
          <div className="step-dots">
            {[1, 2, 3].map((i) => <span key={i} className={`dot ${i === step ? 'active' : ''}`} />)}
          </div>
          <button className="ghost" onClick={restart}>↻ Сбросить</button>
        </div>
      </div>

      <div className="stage">
        <div className="container">
          <div className="page-head">
            <button className={`back-btn ${step === 1 ? 'hidden' : ''}`} onClick={() => setStep(step - 1)}>‹</button>
            <div><div className="page-title">{title}</div><div className="page-sub">{sub}</div></div>
          </div>

          {step === 1 && (
            <div className="form-narrow">
              <div className="wizard-grid">
                <div className="input"><div className="input-icon">📍</div><div className="input-content"><div className="input-label">Откуда</div><div className="input-value">Алматы</div></div></div>
                <div className="input"><div className="input-icon">🏙️</div><div className="input-content"><div className="input-label">Куда</div><div className="input-value">Астана</div></div></div>
                <div className="input"><div className="input-icon">📅</div><div className="input-content"><div className="input-label">Туда</div><div className="input-value">4 июня, чт · 20:00</div></div></div>
                <div className="input"><div className="input-icon">📅</div><div className="input-content"><div className="input-label">Обратно</div><div className="input-value">7 июня, вс</div></div></div>
                <div className="input static full">
                  <div className="input-icon">👨‍👩‍👧‍👦</div>
                  <div className="input-content">
                    <div className="input-label">Кто едет</div>
                    <div className="input-value">Семья · 4 человека</div>
                    <div className="family">
                      <div className="avatar">А</div><div className="avatar">Ал</div>
                      <div className="avatar k">9</div><div className="avatar k">5</div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="btn" onClick={() => setStep(2)}>Найти билеты →</div>
              <div className="wizard-foot">Сначала билет — затем AI соберёт отель, трансфер, страховку и развлечения вокруг него</div>
            </div>
          )}

          {step === 2 && (
            <div className="narrow">
              <div className="tabs">
                {(['avia', 'zhd', 'bus'] as Transport[]).map((tr) => (
                  <div key={tr} className={`tab ${transport === tr ? 'active' : ''}`} onClick={() => pickTransport(tr)}>
                    {tr === 'avia' ? '✈️ Авиа' : tr === 'zhd' ? '🚄 ЖД' : '🚌 Автобус'}
                  </div>
                ))}
              </div>
              <div>
                {TICKETS[transport].map((tk) => (
                  <TicketCard key={tk.id} t={tk} selected={tk.id === ticketId} onClick={() => setTicketId(tk.id)} />
                ))}
              </div>
              <div className="btn" onClick={() => setStep(3)}>Выбрать билет →</div>
            </div>
          )}

          {step === 3 && (
            <div className="grid-side">
              <div className="main">
                <div className="card">
                  <div className="card-title">{icon(transport)} {t.carrier}</div>
                  <Legs t={t} />
                </div>
                <div className="card">
                  <div className="card-title">Пассажиры · 4</div>
                  {PASSENGERS.map((p) => (
                    <div className="pax" key={p.name}>
                      <div className={`avatar ${p.kid ? 'k' : ''}`}>{p.av}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>{p.name}</div>
                        <div style={{ fontSize: 12, color: 'var(--muted)' }}>{p.sub}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <aside className="side">
                <div className="panel">
                  <div className="panel-title">К оплате</div>
                  <div className="stat-row"><span className="stat-label">Билет × 4</span><span className="stat-value">{fmt(t.price)}</span></div>
                  <div className="stat-row" style={{ borderTop: '1px solid var(--border)' }}><span className="stat-label">Сервисный сбор</span><span className="stat-value">0 ₸</span></div>
                  <div className="stat-row" style={{ borderTop: '1px solid var(--border)' }}><span className="stat-label" style={{ fontWeight: 700 }}>Итого</span><span className="stat-value">{fmt(t.price)}</span></div>
                  <div className="pay-method">Способ оплаты</div>
                  <div className="toggle-row disabled"><div><div style={{ fontSize: 14, fontWeight: 600 }}>Купить в рассрочку</div><div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>До 12 месяцев</div></div><div className="toggle" /></div>
                  <div className="toggle-row disabled"><div><div style={{ fontSize: 14, fontWeight: 600 }}>Купить в кредит</div><div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>До 60 месяцев</div></div><div className="toggle" /></div>
                  <div className="panel-note">🎫 Билеты придут в Halyk Wallet и добавятся в план.</div>
                  <div className="btn" onClick={onBuy}>Купить билет · {fmt(t.price)}</div>
                </div>
              </aside>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
