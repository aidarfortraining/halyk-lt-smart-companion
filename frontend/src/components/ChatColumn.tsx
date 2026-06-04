import { useEffect, useRef } from 'react'
import { useTrip } from '../state/trip'
import { Chips } from './Chips'
import { InputArea } from './InputArea'
import { MessageList } from './MessageList'
import { ResultsScreen } from './ResultsScreen'
import { SimButtons } from './SimButtons'

export function ChatColumn() {
  const { snapshot, busy } = useTrip()
  const msgsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = msgsRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [snapshot, busy])

  return (
    <div className="chat-col">
      <div className="ctop">
        <div className="c-ava">✦</div>
        <div className="c-info">
          <div className="c-name">Halyk Travel AI</div>
          <div className="c-sub">Персональный ассистент поездки</div>
        </div>
        <div className="c-status"><div className="sdot" /><span>{busy ? 'Набирает…' : 'Онлайн'}</span></div>
      </div>

      <div className="msgs" ref={msgsRef}>
        {snapshot && <MessageList messages={snapshot.messages} />}
        {busy && (
          <div className="mrow">
            <div className="mava ai">✦</div>
            <div className="bub ai typ"><div className="dots"><span /><span /><span /></div></div>
          </div>
        )}
        <ResultsScreen />
        <SimButtons />
      </div>

      <Chips />
      <InputArea />
    </div>
  )
}
