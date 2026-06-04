import { useState } from 'react'
import { useTrip } from '../state/trip'

// Visual parity with the prototype; chips drive the flow, so free text is a no-op server-side.
export function InputArea() {
  const { answer, busy } = useTrip()
  const [text, setText] = useState('')
  const send = () => {
    const t = text.trim()
    if (!t || busy) return
    setText('')
    answer(t)
  }
  return (
    <div className="inp-area">
      <div className="inp-row">
        <textarea
          className="inp" rows={1} placeholder="Напишите свой ответ…" value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
        />
        <button className="sbtn" disabled={!text.trim() || busy} onClick={send}>↑</button>
      </div>
    </div>
  )
}
