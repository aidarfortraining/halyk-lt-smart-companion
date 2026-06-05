import { useState } from 'react'
import { useTrip } from '../state/trip'

// Chips drive most steps (free text is then a no-op server-side); a text-input step
// (e.g. typing a stay address) accepts the free text and shows its own placeholder.
export function InputArea() {
  const { snapshot, answer, busy } = useTrip()
  const [text, setText] = useState('')
  const send = () => {
    const t = text.trim()
    if (!t || busy) return
    setText('')
    answer(t)
  }
  const placeholder = snapshot?.input_hint || 'Напишите свой ответ…'
  return (
    <div className="inp-area">
      <div className="inp-row">
        <textarea
          className="inp" rows={1} placeholder={placeholder} value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
        />
        <button className="sbtn" disabled={!text.trim() || busy} onClick={send}>↑</button>
      </div>
    </div>
  )
}
