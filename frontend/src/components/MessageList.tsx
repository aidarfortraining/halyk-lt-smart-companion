import type { Message } from '../types'

function MessageItem({ m }: { m: Message }) {
  switch (m.kind) {
    case 'time':
      return <div className="time-div"><span>{m.text}</span></div>
    case 'concern':
      return (
        <div className="concern">
          <div className="concern-tag">💭 В голове клиента</div>
          <div className="concern-text">«{m.meta.title}»</div>
          {m.meta.sub && <div className="concern-sub">{m.meta.sub}</div>}
        </div>
      )
    case 'sys':
      return <div className={`sys-notice ${m.meta.level ?? ''}`}>{m.text}</div>
    case 'user':
      return (
        <div className="mrow u">
          <div className="mava u">Вы</div>
          <div className="bub u">{m.text}</div>
        </div>
      )
    default: // ai / results
      return (
        <div className="mrow">
          <div className="mava ai">✦</div>
          <div className="bub ai">{m.text}</div>
        </div>
      )
  }
}

export function MessageList({ messages }: { messages: Message[] }) {
  return <>{messages.map((m) => <MessageItem key={m.order} m={m} />)}</>
}
